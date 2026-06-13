from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

from .auth import hash_password, verify_password
from .errors import AuthorizationError, NotFoundError, ValidationError
from .store import CsvStore

Clock = Callable[[], datetime]


@dataclass(frozen=True)
class AuthenticationFailure:
    error: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


class BookRentalService:
    def __init__(self, store: CsvStore, clock: Clock = utc_now) -> None:
        self.store = store
        self.clock = clock

    def users(self, admin_id: int) -> list[dict[str, str]]:
        self.require_role(admin_id, "ADMIN")
        return [{key: value for key, value in row.items() if key != "password_hash"} for row in self.store.read("users")]

    def register_user(
        self, name: str, military_id: str, password: str, password_confirmation: str,
    ) -> dict[str, str]:
        return self._create_user(name, military_id, password, password_confirmation, "USER")

    def create_admin(self, name: str, military_id: str, password: str) -> tuple[dict[str, str], bool]:
        name, military_id = name.strip(), military_id.strip()
        existing = next(
            (row for row in self.store.read("users") if row["military_id"].casefold() == military_id.casefold()),
            None,
        )
        if existing:
            if existing["role"] == "ADMIN":
                return existing, False
            raise ValidationError("이미 사용 중인 군번입니다.")
        return self._create_user(name, military_id, password, password, "ADMIN"), True

    def admin_create_user(
        self, admin_id: int, name: str, military_id: str, password: str, password_confirmation: str,
    ) -> dict[str, str]:
        self.require_role(admin_id, "ADMIN")
        return self._create_user(name, military_id, password, password_confirmation, "USER")

    def _create_user(
        self, name: str, military_id: str, password: str, password_confirmation: str, role: str,
    ) -> dict[str, str]:
        name, military_id = name.strip(), military_id.strip()
        if not name or not military_id:
            raise ValidationError("이름과 군번을 입력해 주세요.")
        if password != password_confirmation:
            raise ValidationError("비밀번호가 일치하지 않습니다.")
        if len(password) < 8:
            raise ValidationError("비밀번호는 8자 이상이어야 합니다.")
        with self.store.transaction():
            users = self.store.read("users")
            if any(row["military_id"].casefold() == military_id.casefold() for row in users if row["military_id"]):
                raise ValidationError("이미 가입된 군번입니다.")
            now = iso(self.clock())
            user = {
                "id": str(self.store.next_id(users)), "name": name, "military_id": military_id,
                "password_hash": hash_password(password), "role": role, "active": "true",
                "created_at": now, "updated_at": now,
            }
            users.append(user)
            self.store.write("users", users)
            return user

    def authenticate(self, military_id: str, password: str) -> dict[str, str] | AuthenticationFailure:
        """Authenticate without raising for expected credential failures."""
        military_id = military_id.strip()
        user = next(
            (
                row for row in self.store.read("users")
                if row.get("military_id", "").casefold() == military_id.casefold()
            ),
            None,
        )
        if user is None:
            return AuthenticationFailure(error="ACCOUNT_NOT_FOUND")
        if user.get("active", "").lower() != "true":
            return AuthenticationFailure(error="ACCOUNT_INACTIVE")
        if not verify_password(password, user.get("password_hash", "")):
            return AuthenticationFailure(error="INVALID_PASSWORD")
        return {key: value for key, value in user.items() if key != "password_hash"}

    def approved_books(self) -> list[dict[str, str]]:
        return self._enrich_books([row for row in self.store.read("books") if row["status"] == "APPROVED"])

    def lender_books(self, lender_id: int) -> list[dict[str, str]]:
        self.require_role(lender_id, "USER")
        return self._enrich_books([row for row in self.store.read("books") if int(row["lender_id"]) == lender_id])

    def pending_books(self, admin_id: int) -> list[dict[str, str]]:
        self.require_role(admin_id, "ADMIN")
        return self._enrich_books([row for row in self.store.read("books") if row["status"] == "PENDING"])

    def create_book(
        self, lender_id: int, *, title: str, author: str, category: str, description: str,
        book_format: str, total_quantity: int, default_loan_days: int,
        uploaded_file: tuple[str, bytes] | None = None,
    ) -> dict[str, str]:
        self.require_role(lender_id, "USER")
        title, author, category = title.strip(), author.strip(), category.strip()
        if not title or not author or not category:
            raise ValidationError("제목, 저자, 카테고리는 필수입니다.")
        if total_quantity < 1 or default_loan_days < 1:
            raise ValidationError("수량과 대여 기간은 1 이상이어야 합니다.")
        if book_format not in {"PHYSICAL_BOOK", "PDF"}:
            raise ValidationError("지원하지 않는 책 형식입니다.")
        if book_format == "PDF" and uploaded_file is None:
            raise ValidationError("PDF 파일을 업로드해주세요.")
        if uploaded_file and not uploaded_file[0].lower().endswith(".pdf"):
            raise ValidationError("PDF 파일만 업로드할 수 있습니다.")

        with self.store.transaction():
            books = self.store.read("books")
            book_id = self.store.next_id(books)
            file_name = ""
            stored_path = ""
            if uploaded_file:
                file_name, content = uploaded_file
                destination = self.store.upload_dir / f"{book_id}-{uuid4().hex}.pdf"
                destination.write_bytes(content)
                stored_path = str(destination)
            now = iso(self.clock())
            book = {
                "id": str(book_id), "lender_id": str(lender_id), "title": title,
                "author": author, "category": category, "description": description.strip(),
                "format": book_format, "total_quantity": str(total_quantity),
                "available_quantity": str(total_quantity), "default_loan_days": str(default_loan_days),
                "status": "PENDING", "rejection_memo": "", "file_name": file_name,
                "file_path": stored_path, "created_at": now, "updated_at": now,
            }
            books.append(book)
            self.store.write("books", books)
            return book

    def approve_book(self, admin_id: int, book_id: int) -> None:
        with self.store.transaction():
            self.require_role(admin_id, "ADMIN")
            books = self.store.read("books")
            book = self._find(books, book_id, "책")
            if book["status"] != "PENDING":
                raise ValidationError("승인 대기 중인 책만 승인할 수 있습니다.")
            book.update(status="APPROVED", rejection_memo="", updated_at=iso(self.clock()))
            self.store.write("books", books)
            self._log(admin_id, "BOOK_APPROVED", "BOOK", book_id)

    def reject_book(self, admin_id: int, book_id: int, memo: str) -> None:
        if not memo.strip():
            raise ValidationError("거절 사유를 입력해 주세요.")
        with self.store.transaction():
            self.require_role(admin_id, "ADMIN")
            books = self.store.read("books")
            book = self._find(books, book_id, "책")
            if book["status"] != "PENDING":
                raise ValidationError("승인 대기 중인 책만 거절할 수 있습니다.")
            book.update(status="REJECTED", rejection_memo=memo.strip(), updated_at=iso(self.clock()))
            self.store.write("books", books)
            self._log(admin_id, "BOOK_REJECTED", "BOOK", book_id, memo.strip())

    def create_borrow_request(self, borrower_id: int, book_id: int, quantity: int) -> dict[str, str]:
        self.require_role(borrower_id, "USER")
        if quantity < 1:
            raise ValidationError("대여 수량은 1 이상이어야 합니다.")
        with self.store.transaction():
            books = self.store.read("books")
            book = self._find(books, book_id, "책")
            if book["status"] != "APPROVED":
                raise ValidationError("승인된 책만 대여 요청할 수 있습니다.")
            if quantity > int(book["available_quantity"]):
                raise ValidationError("현재 대여 가능한 수량보다 많이 요청할 수 없습니다.")
            requests = self.store.read("borrow_requests")
            if any(
                int(row["borrower_id"]) == borrower_id and int(row["book_id"]) == book_id
                and row["status"] == "REQUESTED" for row in requests
            ):
                raise ValidationError("이미 처리 대기 중인 대여 요청이 있습니다.")
            now = iso(self.clock())
            request = {
                "id": str(self.store.next_id(requests)), "borrower_id": str(borrower_id),
                "book_id": str(book_id), "quantity": str(quantity), "status": "REQUESTED",
                "requested_at": now, "approved_at": "", "rejected_at": "",
                "canceled_at": "", "rejection_memo": "", "updated_at": now,
            }
            requests.append(request)
            self.store.write("borrow_requests", requests)
            return request

    def borrower_requests(self, borrower_id: int) -> list[dict[str, str]]:
        self.require_role(borrower_id, "USER")
        rows = [row for row in self.store.read("borrow_requests") if int(row["borrower_id"]) == borrower_id]
        return self._enrich_requests(rows)

    def all_requests(self, admin_id: int) -> list[dict[str, str]]:
        self.require_role(admin_id, "ADMIN")
        return self._enrich_requests(self.store.read("borrow_requests"))

    def approve_request(self, admin_id: int, request_id: int) -> dict[str, str]:
        with self.store.transaction():
            self.require_role(admin_id, "ADMIN")
            requests = self.store.read("borrow_requests")
            request = self._find(requests, request_id, "대여 요청")
            if request["status"] != "REQUESTED":
                raise ValidationError("처리 대기 중인 요청만 승인할 수 있습니다.")
            books = self.store.read("books")
            book = self._find(books, int(request["book_id"]), "책")
            quantity, available = int(request["quantity"]), int(book["available_quantity"])
            if book["status"] != "APPROVED" or available < quantity:
                raise ValidationError("승인할 수 없거나 대여 가능한 수량이 부족합니다.")
            now_dt = self.clock()
            now = iso(now_dt)
            book.update(available_quantity=str(available - quantity), updated_at=now)
            request.update(status="APPROVED", approved_at=now, updated_at=now)
            loans = self.store.read("loans")
            loan = {
                "id": str(self.store.next_id(loans)), "borrow_request_id": request["id"],
                "borrower_id": request["borrower_id"], "lender_id": book["lender_id"],
                "book_id": book["id"], "quantity": request["quantity"], "loaned_at": now,
                "due_at": iso(now_dt + timedelta(days=int(book["default_loan_days"]))),
                "returned_at": "", "status": "LOANED", "updated_at": now,
            }
            loans.append(loan)
            self.store.write("books", books)
            self.store.write("borrow_requests", requests)
            self.store.write("loans", loans)
            self._log(admin_id, "BORROW_REQUEST_APPROVED", "BORROW_REQUEST", request_id)
            return loan

    def reject_request(self, admin_id: int, request_id: int, memo: str) -> None:
        if not memo.strip():
            raise ValidationError("거절 사유를 입력해 주세요.")
        with self.store.transaction():
            self.require_role(admin_id, "ADMIN")
            requests = self.store.read("borrow_requests")
            request = self._find(requests, request_id, "대여 요청")
            if request["status"] != "REQUESTED":
                raise ValidationError("처리 대기 중인 요청만 거절할 수 있습니다.")
            now = iso(self.clock())
            request.update(status="REJECTED", rejected_at=now, rejection_memo=memo.strip(), updated_at=now)
            self.store.write("borrow_requests", requests)
            self._log(admin_id, "BORROW_REQUEST_REJECTED", "BORROW_REQUEST", request_id, memo.strip())

    def loans(self, actor_id: int, *, admin: bool = False) -> list[dict[str, str]]:
        self.require_role(actor_id, "ADMIN" if admin else "USER")
        self._sync_overdue()
        rows = self.store.read("loans")
        if not admin:
            rows = [row for row in rows if int(row["borrower_id"]) == actor_id]
        return self._enrich_loans(rows)

    def pdf_download(self, actor_id: int, loan_id: int) -> tuple[str, bytes]:
        loan = self._find(self.store.read("loans"), loan_id, "대출")
        actor = self._user(actor_id)
        if actor["active"].lower() != "true" or (
            actor["role"] != "ADMIN" and int(loan["borrower_id"]) != actor_id
        ):
            raise AuthorizationError("해당 PDF를 다운로드할 권한이 없습니다.")
        if loan["status"] not in {"LOANED", "OVERDUE"}:
            raise AuthorizationError("현재 대여 중인 PDF만 다운로드할 수 있습니다.")
        book = self._find(self.store.read("books"), int(loan["book_id"]), "책")
        if book["format"] != "PDF":
            raise ValidationError("PDF 형식의 책이 아닙니다.")
        path = Path(book["file_path"])
        if not book["file_path"] or not path.is_file():
            raise NotFoundError("PDF 파일을 찾을 수 없습니다.")
        return book["file_name"] or f"{book['title']}.pdf", path.read_bytes()

    def return_book(self, actor_id: int, loan_id: int) -> None:
        with self.store.transaction():
            loans = self.store.read("loans")
            loan = self._find(loans, loan_id, "대출")
            user = self._user(actor_id)
            if user["role"] != "ADMIN" and int(loan["borrower_id"]) != actor_id:
                raise AuthorizationError("대여자 또는 관리자만 반납 처리할 수 있습니다.")
            if loan["status"] not in {"LOANED", "OVERDUE"}:
                raise ValidationError("대여 중이거나 연체된 책만 반납할 수 있습니다.")
            books = self.store.read("books")
            book = self._find(books, int(loan["book_id"]), "책")
            now = iso(self.clock())
            book.update(available_quantity=str(int(book["available_quantity"]) + int(loan["quantity"])), updated_at=now)
            loan.update(status="RETURNED", returned_at=now, updated_at=now)
            self.store.write("books", books)
            self.store.write("loans", loans)

    def dashboard(self, admin_id: int) -> dict[str, int]:
        self.require_role(admin_id, "ADMIN")
        self._sync_overdue()
        users, books = self.store.read("users"), self.store.read("books")
        requests, loans = self.store.read("borrow_requests"), self.store.read("loans")
        return {
            "전체 사용자": len(users), "일반 회원": sum(row["role"] == "USER" for row in users),
            "관리자": sum(row["role"] == "ADMIN" for row in users), "전체 책": len(books),
            "승인 대기 책": sum(row["status"] == "PENDING" for row in books), "대여 요청": len(requests),
            "대여 중": sum(row["status"] == "LOANED" for row in loans),
            "연체": sum(row["status"] == "OVERDUE" for row in loans),
            "반납 완료": sum(row["status"] == "RETURNED" for row in loans),
        }

    def require_role(self, user_id: int, role: str) -> dict[str, str]:
        user = self._user(user_id)
        if user["active"].lower() != "true" or user["role"] != role:
            raise AuthorizationError("이 기능에 접근할 권한이 없습니다.")
        return user

    def _sync_overdue(self) -> None:
        with self.store.transaction():
            loans = self.store.read("loans")
            changed, now = False, self.clock()
            for loan in loans:
                if loan["status"] == "LOANED" and parse_time(loan["due_at"]) < now:
                    loan.update(status="OVERDUE", updated_at=iso(now))
                    changed = True
            if changed:
                self.store.write("loans", loans)

    def _log(self, admin_id: int, action: str, target_type: str, target_id: int, memo: str = "") -> None:
        logs = self.store.read("admin_logs")
        logs.append({
            "id": str(self.store.next_id(logs)), "admin_id": str(admin_id), "action": action,
            "target_type": target_type, "target_id": str(target_id), "memo": memo,
            "created_at": iso(self.clock()),
        })
        self.store.write("admin_logs", logs)

    def _user(self, user_id: int) -> dict[str, str]:
        return self._find(self.store.read("users"), user_id, "사용자")

    @staticmethod
    def _find(rows: list[dict[str, str]], row_id: int, label: str) -> dict[str, str]:
        row = next((item for item in rows if int(item["id"]) == row_id), None)
        if row is None:
            raise NotFoundError(f"{label} ID {row_id}을(를) 찾을 수 없습니다.")
        return row

    def _enrich_books(self, rows: list[dict[str, str]]) -> list[dict[str, str]]:
        users = {row["id"]: row for row in self.store.read("users")}
        return sorted(
            [{**row, "lender_name": users.get(row["lender_id"], {}).get("name", "-")} for row in rows],
            key=lambda row: row["created_at"], reverse=True,
        )

    def _enrich_requests(self, rows: list[dict[str, str]]) -> list[dict[str, str]]:
        users = {row["id"]: row for row in self.store.read("users")}
        books = {row["id"]: row for row in self.store.read("books")}
        return sorted([
            {**row, "borrower_name": users.get(row["borrower_id"], {}).get("name", "-"),
             "book_title": books.get(row["book_id"], {}).get("title", "-")} for row in rows
        ], key=lambda row: row["requested_at"], reverse=True)

    def _enrich_loans(self, rows: list[dict[str, str]]) -> list[dict[str, str]]:
        users = {row["id"]: row for row in self.store.read("users")}
        books = {row["id"]: row for row in self.store.read("books")}
        return sorted([
            {**row, "borrower_name": users.get(row["borrower_id"], {}).get("name", "-"),
             "lender_name": users.get(row["lender_id"], {}).get("name", "-"),
             "book_title": books.get(row["book_id"], {}).get("title", "-"),
             "book_format": books.get(row["book_id"], {}).get("format", "")} for row in rows
        ], key=lambda row: row["due_at"])
