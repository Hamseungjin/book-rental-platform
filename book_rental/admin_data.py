from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .auth import hash_password
from .errors import AuthorizationError, ValidationError
from .store import BOOK_FORMAT_PDF, BOOK_FORMAT_PHYSICAL, BOOK_FORMATS, SCHEMAS, CsvStore

EDITABLE_TABLES = {"users", "books", "borrow_requests", "loans"}
MANAGED_TABLES = EDITABLE_TABLES | {"admin_logs", "pdf_access_logs"}
ALLOWED_STATUSES = {
    "borrow_requests": {"REQUESTED", "APPROVED", "REJECTED", "CANCELED"},
    "loans": {"LOANED", "OVERDUE", "RETURNED"},
}


class AdminDataService:
    """Validated administrator CRUD for the CSV files used by the running app."""

    def __init__(self, store: CsvStore, clock: Callable[[], datetime] | None = None) -> None:
        self.store = store
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def read_table(self, actor: dict[str, object], table: str) -> list[dict[str, str]]:
        self._require_admin(actor)
        self._require_table(table)
        rows = self.store.read(table)
        if table == "users":
            return [{**row, "password_hash": "••••••••"} for row in rows]
        return rows

    def save_table(self, actor: dict[str, object], table: str, rows: list[dict[str, object]]) -> Path:
        self._require_admin(actor)
        if table not in EDITABLE_TABLES:
            raise AuthorizationError("관리자 로그와 PDF 이용 기록은 조회 전용입니다.")
        normalized = self._normalize_and_validate(table, rows)
        self._validate_references(table, normalized)
        with self.store.transaction():
            before = self.store.read(table)
            if table == "books":
                self._reject_dangerous_format_changes(before, normalized)
            if table == "users":
                old_hashes = {row["id"]: row["password_hash"] for row in before}
                for row in normalized:
                    supplied = row["password_hash"]
                    if supplied in {"", "••••••••"} and row["id"] in old_hashes:
                        row["password_hash"] = old_hashes[row["id"]]
                    elif not supplied.startswith("pbkdf2_sha256$"):
                        raise ValidationError("password_hash에는 평문 비밀번호를 저장할 수 없습니다. 비밀번호 재설정을 사용해주세요.")
            backup = self._backup(table)
            self.store.write(table, normalized)
            self._log_changes(actor, table, before, normalized)
            return backup

    def create_user(self, actor: dict[str, object], name: str, military_id: str, password: str, role: str = "USER") -> dict[str, str]:
        self._require_admin(actor)
        name, military_id = name.strip(), military_id.strip()
        if not name or not military_id:
            raise ValidationError("이름과 군번을 입력해 주세요.")
        if len(password) < 8:
            raise ValidationError("비밀번호는 8자 이상이어야 합니다.")
        if role not in {"USER", "ADMIN"}:
            raise ValidationError("사용자 role은 USER 또는 ADMIN만 가능합니다.")
        with self.store.transaction():
            users = self.store.read("users")
            if any(row["military_id"].casefold() == military_id.casefold() for row in users):
                raise ValidationError("users.csv의 military_id는 중복될 수 없습니다.")
            now = self.clock().astimezone(timezone.utc).isoformat(timespec="seconds")
            user = {
                "id": str(self.store.next_id(users)), "name": name, "military_id": military_id,
                "password_hash": hash_password(password), "role": role, "active": "true",
                "created_at": now, "updated_at": now,
            }
            self._backup("users")
            users.append(user)
            self.store.write("users", users)
            self._append_log(actor, "CSV_ROW_ADDED", "users.csv", user["id"], None, user)
            return {key: value for key, value in user.items() if key != "password_hash"}

    def reset_password(self, actor: dict[str, object], user_id: int, new_password: str) -> None:
        self._require_admin(actor)
        if len(new_password) < 8:
            raise ValidationError("비밀번호는 8자 이상이어야 합니다.")
        with self.store.transaction():
            users = self.store.read("users")
            user = next((row for row in users if int(row["id"]) == user_id), None)
            if user is None:
                raise ValidationError("사용자를 찾을 수 없습니다.")
            before = dict(user)
            user["password_hash"] = hash_password(new_password)
            user["updated_at"] = self.clock().astimezone(timezone.utc).isoformat(timespec="seconds")
            self._backup("users")
            self.store.write("users", users)
            self._append_log(actor, "PASSWORD_RESET", "users.csv", str(user_id), before, {**user, "password_hash": "[변경됨]"})

    def _normalize_and_validate(self, table: str, rows: list[dict[str, object]]) -> list[dict[str, str]]:
        fields = SCHEMAS[table]
        normalized: list[dict[str, str]] = []
        for index, row in enumerate(rows, start=1):
            missing = [field for field in fields if field not in row]
            if missing:
                raise ValidationError(f"{table}.csv의 {index}행에 필수 컬럼이 누락되었습니다: {', '.join(missing)}")
            normalized.append({field: "" if row[field] is None else str(row[field]).strip() for field in fields})
        ids = [row["id"] for row in normalized]
        if any(not value or not value.isdigit() for value in ids):
            raise ValidationError("id 컬럼은 비어 있지 않은 숫자여야 합니다.")
        if len(ids) != len(set(ids)):
            raise ValidationError("id 컬럼은 중복될 수 없습니다.")
        if table == "users":
            military_ids = [row["military_id"].casefold() for row in normalized if row["military_id"]]
            if len(military_ids) != len(set(military_ids)):
                raise ValidationError("users.csv의 military_id는 중복될 수 없습니다.")
            if any(row["role"] not in {"USER", "ADMIN"} for row in normalized):
                raise ValidationError("사용자 role은 USER 또는 ADMIN만 가능합니다.")
        if table == "books":
            for row in normalized:
                if row["format"] not in BOOK_FORMATS:
                    raise ValidationError("도서 format은 PHYSICAL_BOOK 또는 PDF만 가능합니다.")
                if row["format"] == BOOK_FORMAT_PHYSICAL:
                    try:
                        total = int(row["total_quantity"])
                        available = int(row["available_quantity"])
                        loan_days = int(row["default_loan_days"])
                    except ValueError as exc:
                        raise ValidationError("실물 도서 수량과 대여 기간은 정수여야 합니다.") from exc
                    if total < 1:
                        raise ValidationError("실물 도서 총수량은 1 이상이어야 합니다.")
                    if available < 0 or available > total:
                        raise ValidationError("실물 도서 대여 가능 수량은 0 이상이고 총 수량을 초과할 수 없습니다.")
                    if loan_days < 1:
                        raise ValidationError("실물 도서 기본 대여 기간은 1일 이상이어야 합니다.")
                if row["format"] == BOOK_FORMAT_PDF:
                    self._validate_pdf_row(row)
        if table in ALLOWED_STATUSES and any(row["status"] not in ALLOWED_STATUSES[table] for row in normalized):
            allowed = ", ".join(sorted(ALLOWED_STATUSES[table]))
            raise ValidationError(f"{table}.csv의 status는 다음 값만 가능합니다: {allowed}")
        return normalized

    def _validate_references(self, table: str, rows: list[dict[str, str]]) -> None:
        if table not in {"borrow_requests", "loans"}:
            return
        books = {row["id"]: row for row in self.store.read("books")}
        for row in rows:
            book = books.get(row["book_id"])
            if book is None:
                raise ValidationError(f"{table}.csv가 존재하지 않는 book_id를 참조합니다: {row['book_id']}")
            if book["format"] != BOOK_FORMAT_PHYSICAL:
                raise ValidationError(f"{table}.csv는 실물 도서만 참조할 수 있습니다.")

    def _reject_dangerous_format_changes(self, before: list[dict[str, str]], after: list[dict[str, str]]) -> None:
        before_by_id = {row["id"]: row for row in before}
        referenced_book_ids = {row["book_id"] for row in self.store.read("borrow_requests")} | {
            row["book_id"] for row in self.store.read("loans")
        }
        for row in after:
            old = before_by_id.get(row["id"])
            if old and old.get("format") != row.get("format") and row["id"] in referenced_book_ids:
                raise ValidationError("요청 또는 대출 기록이 있는 도서의 형식은 변경할 수 없습니다.")

    def _validate_pdf_row(self, row: dict[str, str]) -> None:
        if not row["file_path"]:
            raise ValidationError("PDF 자료는 file_path가 필요합니다.")
        upload_root = self.store.upload_dir.resolve()
        try:
            path = Path(row["file_path"]).expanduser().resolve()
        except OSError as exc:
            raise ValidationError("PDF file_path가 올바르지 않습니다.") from exc
        if not path.is_relative_to(upload_root):
            raise ValidationError("PDF file_path는 업로드 디렉터리 내부여야 합니다.")
        if not path.is_file():
            raise ValidationError("PDF 파일을 찾을 수 없습니다.")

    def _backup(self, table: str) -> Path:
        backup_dir = self.store.data_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = self.clock().astimezone(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        destination = backup_dir / f"{table}_{stamp}.csv"
        shutil.copy2(self.store.path(table), destination)
        return destination

    def _log_changes(self, actor: dict[str, object], table: str, before: list[dict[str, str]], after: list[dict[str, str]]) -> None:
        before_by_id, after_by_id = ({r["id"]: r for r in before}, {r["id"]: r for r in after})
        for row_id in sorted(before_by_id.keys() | after_by_id.keys(), key=lambda value: int(value)):
            old, new = before_by_id.get(row_id), after_by_id.get(row_id)
            if old == new:
                continue
            action = "CSV_ROW_ADDED" if old is None else "CSV_ROW_DELETED" if new is None else "CSV_ROW_UPDATED"
            self._append_log(actor, action, f"{table}.csv", row_id, old, new)

    def _append_log(self, actor: dict[str, object], action: str, target_file: str, target_id: str, before, after) -> None:
        logs = self.store.read("admin_logs")
        now = self.clock().astimezone(timezone.utc).isoformat(timespec="seconds")
        def summary(value):
            if value is None:
                return ""
            safe = {k: ("[숨김]" if k == "password_hash" else v) for k, v in value.items()}
            return json.dumps(safe, ensure_ascii=False, sort_keys=True)[:2000]
        logs.append({
            "id": str(self.store.next_id(logs)), "admin_id": str(actor["id"]), "admin_name": actor.get("name", ""),
            "action": action, "target_type": "CSV_ROW", "target_file": target_file, "target_id": target_id,
            "memo": "관리자 데이터 관리", "before_summary": summary(before), "after_summary": summary(after), "created_at": now,
        })
        self.store.write("admin_logs", logs)

    @staticmethod
    def _require_admin(actor: dict[str, object] | None) -> None:
        """Authorize both legacy string and normalized boolean session users.

        Do not delegate this session-boundary check to ``CsvStore.is_active``:
        mixed deployments may still have the older string-only store helper.
        """
        if not actor or str(actor.get("role", "")).strip().upper() != "ADMIN":
            raise AuthorizationError("권한이 없습니다.")
        active = actor.get("active", True)
        is_active = active if isinstance(active, bool) else str(active).strip().casefold() in {
            "true", "1", "yes", "y", "on",
        }
        if not is_active:
            raise AuthorizationError("권한이 없습니다.")

    @staticmethod
    def _require_table(table: str) -> None:
        if table not in MANAGED_TABLES:
            raise ValidationError("관리할 수 없는 CSV 파일입니다.")
