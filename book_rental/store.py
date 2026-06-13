from __future__ import annotations

import csv
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import fcntl

from .config import get_data_dir

SCHEMAS: dict[str, list[str]] = {
    "users": [
        "id", "name", "military_id", "password_hash", "role", "active",
        "created_at", "updated_at",
    ],
    "books": [
        "id", "lender_id", "title", "author", "category", "description", "format",
        "total_quantity", "available_quantity", "default_loan_days", "status",
        "rejection_memo", "file_name", "file_path", "created_at", "updated_at",
    ],
    "borrow_requests": [
        "id", "borrower_id", "book_id", "quantity", "status", "requested_at",
        "approved_at", "rejected_at", "canceled_at", "rejection_memo", "updated_at",
    ],
    "loans": [
        "id", "borrow_request_id", "borrower_id", "lender_id", "book_id", "quantity",
        "loaned_at", "due_at", "returned_at", "status", "updated_at",
    ],
    "admin_logs": [
        "id", "admin_id", "admin_name", "action", "target_type", "target_file", "target_id",
        "memo", "before_summary", "after_summary", "created_at",
    ],
    "sessions": [
        "token_hash", "user_id", "military_id", "role", "created_at", "expires_at",
        "revoked_at", "last_seen_at",
    ],
}


class CsvStore:
    """Small CSV data store with schema migration, locking, and atomic replacement."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir).expanduser().resolve() if data_dir is not None else get_data_dir()
        self.upload_dir = self.data_dir / "uploads"
        self.lock_path = self.data_dir / ".bookbridge.lock"
        self.initialize()

    def initialize(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        for table, fields in SCHEMAS.items():
            path = self.path(table)
            if not path.exists():
                self._write_file(path, fields, [])
            else:
                self._migrate_file(table, path, fields)

    def _migrate_file(self, table: str, path: Path, fields: list[str]) -> None:
        with path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            old_fields = reader.fieldnames or []
            rows = list(reader)
        if old_fields == fields:
            return
        if table == "users":
            for row in rows:
                legacy_roles = set(filter(None, row.get("roles", "").split("|")))
                role = row.get("role", "").upper()
                if role not in {"ADMIN", "USER"}:
                    role = "ADMIN" if "ADMIN" in legacy_roles else "USER"
                row["role"] = role
                row["military_id"] = row.get("military_id", "")
                row["password_hash"] = row.get("password_hash", "")
                row["active"] = row.get("active") or "true"
                row["created_at"] = row.get("created_at", "")
                row["updated_at"] = row.get("updated_at", "")
        self._write_file(path, fields, rows)

    def path(self, table: str) -> Path:
        if table not in SCHEMAS:
            raise KeyError(f"Unknown table: {table}")
        return self.data_dir / f"{table}.csv"

    def ensure_table(self, table: str) -> Path:
        """Create or migrate one table that may have been removed after startup."""
        path = self.path(table)
        if not path.exists():
            self._write_file(path, SCHEMAS[table], [])
        else:
            self._migrate_file(table, path, SCHEMAS[table])
        return path

    def read(self, table: str) -> list[dict[str, str]]:
        with self.path(table).open(encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def write(self, table: str, rows: list[dict[str, object]]) -> None:
        self._write_file(self.path(table), SCHEMAS[table], rows)

    @staticmethod
    def is_active(value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().casefold() in {"true", "1", "yes", "y", "on"}

    def read_users(self) -> list[dict[str, str]]:
        """Read users with stable string IDs and safe defaults for legacy rows."""
        rows = self.read("users")
        required = {"id", "name", "military_id", "password_hash"}
        fields = set(rows[0]) if rows else set(SCHEMAS["users"])
        missing = sorted(required - fields)
        if missing:
            raise ValueError(f"users.csv 필수 컬럼이 누락되었습니다: {', '.join(missing)}")
        normalized = []
        for row in rows:
            normalized.append({
                **row,
                "id": str(row.get("id", "")).strip(),
                "name": str(row.get("name", "")).strip(),
                "military_id": str(row.get("military_id", "")).strip(),
                "password_hash": str(row.get("password_hash", "")).strip(),
                "role": str(row.get("role", "")).strip().upper() or "USER",
                "active": "true" if self.is_active(row.get("active", "true")) else "false",
                "created_at": str(row.get("created_at", "")),
                "updated_at": str(row.get("updated_at", "")),
            })
        return normalized

    def next_id(self, rows: list[dict[str, str]]) -> int:
        return max((int(row["id"]) for row in rows if row.get("id", "").isdigit()), default=0) + 1

    @contextmanager
    def transaction(self) -> Iterator["CsvStore"]:
        """Serialize mutations and restore every CSV if a mutation fails."""
        with self.lock_path.open("r+") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            backup_dir = Path(tempfile.mkdtemp(prefix="bookbridge-backup-"))
            try:
                for table in SCHEMAS:
                    shutil.copy2(self.path(table), backup_dir / f"{table}.csv")
                yield self
            except Exception:
                for table in SCHEMAS:
                    os.replace(backup_dir / f"{table}.csv", self.path(table))
                raise
            finally:
                shutil.rmtree(backup_dir, ignore_errors=True)
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _write_file(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                for row in rows:
                    writer.writerow({field: row.get(field, "") for field in fields})
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
