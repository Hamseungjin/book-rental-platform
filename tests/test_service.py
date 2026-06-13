from __future__ import annotations

import csv
from pathlib import Path
from datetime import datetime, timezone

import pytest

from book_rental.admin_command_runner import resolve_data_dir
from book_rental.auth import verify_password
from book_rental.config import DEFAULT_DATA_DIR, get_data_dir
from book_rental.errors import AuthorizationError, NotFoundError, ValidationError
from book_rental.service import BookRentalService
from book_rental.store import CsvStore

NOW = datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def service(tmp_path):
    instance = BookRentalService(CsvStore(tmp_path / "data"), clock=lambda: NOW)
    admin, _ = instance.create_admin("관리자", "admin", "admin1234")
    member = instance.register_user("홍승진", "25-12345678", "member1234", "member1234")
    instance.admin_id = int(admin["id"])
    instance.member_id = int(member["id"])
    return instance


def create_approved_book(service, quantity=2, *, pdf=False):
    book = service.create_book(
        service.member_id,
        title="도메인 주도 설계",
        author="Eric Evans",
        category="소프트웨어",
        description="DDD 참고서",
        book_format="PDF" if pdf else "PHYSICAL_BOOK",
        total_quantity=quantity,
        default_loan_days=14,
        uploaded_file=("ddd.pdf", b"%PDF-1.4 test") if pdf else None,
    )
    service.approve_book(service.admin_id, int(book["id"]))
    return book


def test_registration_succeeds_and_password_is_hashed(tmp_path):
    service = BookRentalService(CsvStore(tmp_path / "data"), clock=lambda: NOW)

    user = service.register_user("김병장", "24-00000001", "safe-pass", "safe-pass")
    stored = service.store.read("users")[0]

    assert user["role"] == "USER"
    assert user["active"] == "true"
    assert user["created_at"] == user["updated_at"] == NOW.isoformat(timespec="seconds")
    assert stored["password_hash"] != "safe-pass"
    assert verify_password("safe-pass", stored["password_hash"])


def test_duplicate_military_id_registration_fails(service):
    with pytest.raises(ValidationError, match="이미 가입된 군번"):
        service.register_user("중복 사용자", "25-12345678", "password1", "password1")


def test_password_confirmation_mismatch_fails(tmp_path):
    service = BookRentalService(CsvStore(tmp_path / "data"), clock=lambda: NOW)

    with pytest.raises(ValidationError, match="비밀번호가 일치하지 않습니다"):
        service.register_user("김병장", "24-00000001", "password1", "password2")


def test_login_succeeds_without_exposing_password_hash(service):
    result = service.authenticate("25-12345678", "member1234")

    assert result["name"] == "홍승진"
    assert "password_hash" not in result


def test_login_with_wrong_password_fails_without_exception(service):
    result = service.authenticate("25-12345678", "wrong-password")

    assert result.error == "INVALID_PASSWORD"


def test_login_with_unknown_military_id_fails_without_exception(service):
    result = service.authenticate("not-a-member", "member1234")

    assert result.error == "ACCOUNT_NOT_FOUND"


def test_regular_user_cannot_access_admin_features(service):
    with pytest.raises(AuthorizationError):
        service.dashboard(service.member_id)
    with pytest.raises(AuthorizationError):
        service.users(service.member_id)
    with pytest.raises(AuthorizationError):
        service.pending_books(service.member_id)


def test_admin_can_add_a_regular_user(service):
    user = service.admin_create_user(
        service.admin_id, "추가 사용자", "26-00000002", "temporary1", "temporary1",
    )

    assert user["role"] == "USER"
    assert service.authenticate("26-00000002", "temporary1")["id"] == user["id"]


def test_regular_user_can_register_and_borrow_books(service):
    book = create_approved_book(service)

    request = service.create_borrow_request(service.member_id, int(book["id"]), 1)

    assert service.lender_books(service.member_id)[0]["id"] == book["id"]
    assert service.borrower_requests(service.member_id)[0]["id"] == request["id"]


def test_complete_loan_lifecycle_restores_inventory(service):
    book = create_approved_book(service)
    request = service.create_borrow_request(service.member_id, int(book["id"]), 1)
    loan = service.approve_request(service.admin_id, int(request["id"]))

    assert loan["status"] == "LOANED"
    assert service.approved_books()[0]["available_quantity"] == "1"

    service.return_book(service.member_id, int(loan["id"]))

    assert service.loans(service.member_id)[0]["status"] == "RETURNED"
    assert service.approved_books()[0]["available_quantity"] == "2"


def test_second_approval_fails_without_partial_csv_updates(service):
    second = service.register_user("두 번째 회원", "25-87654321", "password2", "password2")
    book = create_approved_book(service, quantity=1)
    first_request = service.create_borrow_request(service.member_id, int(book["id"]), 1)
    second_request = service.create_borrow_request(int(second["id"]), int(book["id"]), 1)
    service.approve_request(service.admin_id, int(first_request["id"]))

    with pytest.raises(ValidationError, match="수량이 부족"):
        service.approve_request(service.admin_id, int(second_request["id"]))

    failed = next(row for row in service.all_requests(service.admin_id) if row["id"] == second_request["id"])
    assert failed["status"] == "REQUESTED"
    assert len(service.loans(service.admin_id, admin=True)) == 1


def test_approved_pdf_is_downloadable_only_by_borrower_and_admin(service):
    other = service.register_user("다른 회원", "25-22222222", "password2", "password2")
    book = create_approved_book(service, pdf=True)
    request = service.create_borrow_request(service.member_id, int(book["id"]), 1)
    loan = service.approve_request(service.admin_id, int(request["id"]))

    filename, content = service.pdf_download(service.member_id, int(loan["id"]))
    assert filename == "ddd.pdf"
    assert content.startswith(b"%PDF")
    assert service.pdf_download(service.admin_id, int(loan["id"]))[1] == content
    with pytest.raises(AuthorizationError, match="권한"):
        service.pdf_download(int(other["id"]), int(loan["id"]))


def test_missing_pdf_file_returns_korean_error(service):
    book = create_approved_book(service, pdf=True)
    request = service.create_borrow_request(service.member_id, int(book["id"]), 1)
    loan = service.approve_request(service.admin_id, int(request["id"]))
    Path(book["file_path"]).unlink()

    with pytest.raises(NotFoundError, match="PDF 파일을 찾을 수 없습니다"):
        service.pdf_download(service.member_id, int(loan["id"]))


def test_returned_pdf_is_no_longer_downloadable(service):
    book = create_approved_book(service, pdf=True)
    request = service.create_borrow_request(service.member_id, int(book["id"]), 1)
    loan = service.approve_request(service.admin_id, int(request["id"]))
    service.return_book(service.member_id, int(loan["id"]))

    with pytest.raises(AuthorizationError, match="대여 중"):
        service.pdf_download(service.member_id, int(loan["id"]))


def test_pdf_requires_a_pdf_upload(service):
    with pytest.raises(ValidationError, match="PDF 파일을 업로드해주세요"):
        service.create_book(
            service.member_id, title="전자책", author="작가", category="에세이", description="",
            book_format="PDF", total_quantity=1, default_loan_days=7,
        )


def test_legacy_user_csv_schema_is_migrated_without_data_loss(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    with (data_dir / "users.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "name", "email", "roles", "active", "created_at", "updated_at"])
        writer.writeheader()
        writer.writerow({
            "id": "7", "name": "기존 등록자", "email": "legacy@example.com", "roles": "LENDER",
            "active": "true", "created_at": "2025-01-01T00:00:00+00:00", "updated_at": "2025-01-01T00:00:00+00:00",
        })

    store = CsvStore(data_dir)
    migrated = store.read("users")[0]

    assert migrated["id"] == "7"
    assert migrated["name"] == "기존 등록자"
    assert migrated["role"] == "USER"
    assert migrated["military_id"] == ""
    assert migrated["password_hash"] == ""


def test_new_store_does_not_seed_demo_users(tmp_path):
    assert CsvStore(tmp_path / "data").read("users") == []


def test_duplicate_admin_creation_is_idempotent(tmp_path):
    service = BookRentalService(CsvStore(tmp_path / "data"), clock=lambda: NOW)

    first, first_created = service.create_admin("관리자", "admin", "admin1234")
    second, second_created = service.create_admin("다른 이름", "admin", "different1234")

    assert first_created is True
    assert second_created is False
    assert first["id"] == second["id"]
    assert len(service.store.read("users")) == 1


def test_overdue_status_is_synchronized_when_loans_are_read(tmp_path):
    approval_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    current_time = [approval_time]
    service = BookRentalService(CsvStore(tmp_path / "data"), clock=lambda: current_time[0])
    admin, _ = service.create_admin("관리자", "admin", "admin1234")
    member = service.register_user("회원", "member", "member123", "member123")
    service.admin_id, service.member_id = int(admin["id"]), int(member["id"])
    book = create_approved_book(service)
    request = service.create_borrow_request(service.member_id, int(book["id"]), 1)
    service.approve_request(service.admin_id, int(request["id"]))
    current_time[0] = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)

    assert service.loans(service.member_id)[0]["status"] == "OVERDUE"


def test_app_store_and_admin_runner_share_environment_data_dir(tmp_path, monkeypatch):
    configured = tmp_path / "shared-data"
    monkeypatch.setenv("BOOKBRIDGE_DATA_DIR", str(configured))

    assert get_data_dir() == configured.resolve()
    assert CsvStore().data_dir == configured.resolve()
    assert resolve_data_dir() == configured.resolve()


def test_default_data_dir_is_project_root_data(monkeypatch):
    monkeypatch.delenv("BOOKBRIDGE_DATA_DIR", raising=False)

    assert get_data_dir() == DEFAULT_DATA_DIR.resolve()
    assert resolve_data_dir() == DEFAULT_DATA_DIR.resolve()


def test_admin_runner_data_dir_argument_overrides_environment(tmp_path, monkeypatch):
    environment_dir = tmp_path / "environment-data"
    command_dir = tmp_path / "command-data"
    monkeypatch.setenv("BOOKBRIDGE_DATA_DIR", str(environment_dir))

    assert resolve_data_dir(str(command_dir)) == command_dir.resolve()


def test_duplicate_active_loan_is_rejected(service):
    book = create_approved_book(service, quantity=2)
    request = service.create_borrow_request(service.member_id, int(book["id"]), 1)
    service.approve_request(service.admin_id, int(request["id"]))

    with pytest.raises(ValidationError, match="중복 대여"):
        service.create_borrow_request(service.member_id, int(book["id"]), 1)
