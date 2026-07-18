from __future__ import annotations

import csv
from pathlib import Path
from datetime import datetime, timezone

import pytest

from book_rental.admin_command_runner import migrate_pdf_loans, resolve_data_dir
from book_rental.auth import verify_password
from book_rental.config import DEFAULT_DATA_DIR, get_data_dir
from book_rental.errors import AuthorizationError, NotFoundError, ValidationError
from book_rental.service import BookRentalService
from book_rental.store import BOOK_FORMAT_PDF, BOOK_FORMAT_PHYSICAL, CsvStore

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
    if pdf:
        book = service.create_book(
            service.member_id,
            title="도메인 주도 설계",
            author="Eric Evans",
            category="소프트웨어",
            description="DDD 참고서",
            book_format=BOOK_FORMAT_PDF,
            uploaded_file=("ddd.pdf", b"%PDF-1.4 test"),
        )
    else:
        book = service.create_book(
            service.member_id,
            title="도메인 주도 설계",
            author="Eric Evans",
            category="소프트웨어",
            description="DDD 참고서",
            book_format=BOOK_FORMAT_PHYSICAL,
            total_quantity=quantity,
            default_loan_days=14,
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

    assert result.succeeded is True
    assert result.user["name"] == "홍승진"
    assert "password_hash" not in result.user


def test_login_with_wrong_password_fails_without_exception(service):
    result = service.authenticate("25-12345678", "wrong-password")

    assert result.status == "INVALID_PASSWORD"


def test_login_with_unknown_military_id_fails_without_exception(service):
    result = service.authenticate("not-a-member", "member1234")

    assert result.status == "ACCOUNT_NOT_FOUND"


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
    assert service.authenticate("26-00000002", "temporary1").user["id"] == user["id"]


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


def test_approved_pdf_is_downloadable_by_active_user_and_admin_without_loan(service):
    other = service.register_user("다른 회원", "25-22222222", "password2", "password2")
    book = create_approved_book(service, pdf=True)
    before = dict(service.store.read("books")[0])

    filename, content = service.pdf_download(service.member_id, int(book["id"]))
    assert filename == "ddd.pdf"
    assert content.startswith(b"%PDF")
    assert service.pdf_download(service.admin_id, int(book["id"]))[1] == content
    assert service.pdf_download(int(other["id"]), int(book["id"]))[1] == content
    assert service.store.read("books")[0]["available_quantity"] == before["available_quantity"]
    assert service.store.read("borrow_requests") == []
    assert service.store.read("loans") == []
    assert len(service.store.read("pdf_access_logs")) == 3


def test_missing_pdf_file_returns_korean_error(service):
    book = create_approved_book(service, pdf=True)
    Path(book["file_path"]).unlink()

    with pytest.raises(NotFoundError, match="PDF 파일을 찾을 수 없습니다"):
        service.pdf_download(service.member_id, int(book["id"]))
    assert service.store.read("pdf_access_logs") == []


def test_pending_and_rejected_pdf_are_not_downloadable(service):
    pending = service.create_book(
        service.member_id, title="대기 PDF", author="작가", category="분류", description="",
        book_format=BOOK_FORMAT_PDF, uploaded_file=("pending.pdf", b"%PDF-1.4 pending"),
    )
    rejected = service.create_book(
        service.member_id, title="거절 PDF", author="작가", category="분류", description="",
        book_format=BOOK_FORMAT_PDF, uploaded_file=("rejected.pdf", b"%PDF-1.4 rejected"),
    )
    service.reject_book(service.admin_id, int(rejected["id"]), "불가")

    with pytest.raises(AuthorizationError, match="승인된 PDF"):
        service.pdf_download(service.member_id, int(pending["id"]))
    with pytest.raises(AuthorizationError, match="승인된 PDF"):
        service.pdf_download(service.member_id, int(rejected["id"]))


def test_pdf_requires_a_pdf_upload(service):
    with pytest.raises(ValidationError, match="PDF 파일을 업로드해주세요"):
        service.create_book(
            service.member_id, title="전자책", author="작가", category="에세이", description="",
            book_format=BOOK_FORMAT_PDF,
        )


def test_pdf_rejects_empty_or_non_pdf_upload(service):
    with pytest.raises(ValidationError, match="빈 PDF"):
        service.create_book(
            service.member_id, title="빈 PDF", author="작가", category="에세이", description="",
            book_format=BOOK_FORMAT_PDF, uploaded_file=("empty.pdf", b""),
        )
    with pytest.raises(ValidationError, match="올바른 PDF"):
        service.create_book(
            service.member_id, title="가짜 PDF", author="작가", category="에세이", description="",
            book_format=BOOK_FORMAT_PDF, uploaded_file=("fake.pdf", b"not pdf"),
        )


def test_pdf_registration_uses_empty_quantity_and_loan_days(service):
    book = service.create_book(
        service.member_id, title="전자책", author="작가", category="에세이", description="",
        book_format=BOOK_FORMAT_PDF, uploaded_file=("ebook.pdf", b"%PDF-1.4 test"),
    )

    assert book["status"] == "PENDING"
    assert book["total_quantity"] == ""
    assert book["available_quantity"] == ""
    assert book["default_loan_days"] == ""


def test_inactive_user_and_admin_cannot_register_pdf_or_physical(service):
    rows = service.store.read("users")
    member = next(row for row in rows if row["id"] == str(service.member_id))
    member["active"] = "false"
    service.store.write("users", rows)

    with pytest.raises(AuthorizationError):
        service.create_book(
            service.member_id, title="전자책", author="작가", category="에세이", description="",
            book_format=BOOK_FORMAT_PDF, uploaded_file=("ebook.pdf", b"%PDF-1.4 test"),
        )
    with pytest.raises(AuthorizationError):
        service.create_book(
            service.admin_id, title="관리자 책", author="작가", category="에세이", description="",
            book_format=BOOK_FORMAT_PHYSICAL, total_quantity=1, default_loan_days=1,
        )


def test_pdf_cannot_enter_physical_loan_flow(service):
    book = create_approved_book(service, pdf=True)

    with pytest.raises(ValidationError, match="PDF 자료는 대여 요청할 수 없습니다"):
        service.create_borrow_request(service.member_id, int(book["id"]), 1)

    requests = service.store.read("borrow_requests")
    requests.append({
        "id": "1", "borrower_id": str(service.member_id), "book_id": book["id"], "quantity": "1",
        "status": "REQUESTED", "requested_at": NOW.isoformat(timespec="seconds"), "approved_at": "",
        "rejected_at": "", "canceled_at": "", "rejection_memo": "", "updated_at": NOW.isoformat(timespec="seconds"),
    })
    service.store.write("borrow_requests", requests)
    with pytest.raises(ValidationError, match="PDF 자료는 대여 승인할 수 없습니다"):
        service.approve_request(service.admin_id, 1)

    loans = service.store.read("loans")
    loans.append({
        "id": "1", "borrow_request_id": "1", "borrower_id": str(service.member_id),
        "lender_id": str(service.member_id), "book_id": book["id"], "quantity": "1",
        "loaned_at": NOW.isoformat(timespec="seconds"), "due_at": NOW.isoformat(timespec="seconds"),
        "returned_at": "", "status": "LOANED", "updated_at": NOW.isoformat(timespec="seconds"),
    })
    service.store.write("loans", loans)
    with pytest.raises(ValidationError, match="PDF 자료는 반납 대상이 아닙니다"):
        service.return_book(service.member_id, 1)


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


def test_pdf_is_excluded_from_overdue_and_dashboard_counts(service):
    book = create_approved_book(service, pdf=True)
    loans = service.store.read("loans")
    loans.append({
        "id": "1", "borrow_request_id": "1", "borrower_id": str(service.member_id),
        "lender_id": str(service.member_id), "book_id": book["id"], "quantity": "1",
        "loaned_at": "2026-01-01T00:00:00+00:00", "due_at": "2026-01-02T00:00:00+00:00",
        "returned_at": "", "status": "LOANED", "updated_at": "2026-01-01T00:00:00+00:00",
    })
    service.store.write("loans", loans)

    assert service.loans(service.member_id) == []
    assert service.store.read("loans")[0]["status"] == "LOANED"
    dashboard = service.dashboard(service.admin_id)
    assert dashboard["대여 중"] == 0
    assert dashboard["연체"] == 0


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


def test_legacy_pdf_book_values_are_read_but_ignored_for_download(service):
    book = create_approved_book(service, pdf=True)
    rows = service.store.read("books")
    rows[0]["total_quantity"] = "1"
    rows[0]["available_quantity"] = "0"
    rows[0]["default_loan_days"] = "14"
    service.store.write("books", rows)

    filename, content = service.pdf_download(service.member_id, int(book["id"]))

    assert filename == "ddd.pdf"
    assert content.startswith(b"%PDF")
    assert service.store.read("books")[0]["available_quantity"] == "0"
    assert service.store.read("loans") == []


def test_pdf_download_rejects_path_outside_upload_dir(service, tmp_path):
    book = create_approved_book(service, pdf=True)
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"%PDF-1.4 outside")
    rows = service.store.read("books")
    rows[0]["file_path"] = str(outside)
    service.store.write("books", rows)

    with pytest.raises(AuthorizationError, match="허용되지 않은"):
        service.pdf_download(service.member_id, int(book["id"]))
    assert service.store.read("pdf_access_logs") == []


def test_migrate_pdf_loans_dry_run_and_apply_are_idempotent(service, capsys):
    physical = create_approved_book(service)
    pdf = create_approved_book(service, pdf=True)
    loans = service.store.read("loans")
    loans.extend([
        {
            "id": "1", "borrow_request_id": "1", "borrower_id": str(service.member_id),
            "lender_id": str(service.member_id), "book_id": pdf["id"], "quantity": "1",
            "loaned_at": NOW.isoformat(timespec="seconds"), "due_at": NOW.isoformat(timespec="seconds"),
            "returned_at": "", "status": "LOANED", "updated_at": NOW.isoformat(timespec="seconds"),
        },
        {
            "id": "2", "borrow_request_id": "2", "borrower_id": str(service.member_id),
            "lender_id": str(service.member_id), "book_id": physical["id"], "quantity": "1",
            "loaned_at": NOW.isoformat(timespec="seconds"), "due_at": NOW.isoformat(timespec="seconds"),
            "returned_at": "", "status": "LOANED", "updated_at": NOW.isoformat(timespec="seconds"),
        },
    ])
    service.store.write("loans", loans)

    assert migrate_pdf_loans(service.store.data_dir, apply=False) == 0
    assert service.store.read("loans")[0]["status"] == "LOANED"
    assert "활성 PDF 대출 수: 1" in capsys.readouterr().out

    assert migrate_pdf_loans(service.store.data_dir, apply=True) == 0
    after = service.store.read("loans")
    assert after[0]["status"] == "RETURNED"
    assert after[1]["status"] == "LOANED"
    assert service.store.read("admin_logs")[-1]["action"] == "PDF_LOAN_MIGRATED"

    assert migrate_pdf_loans(service.store.data_dir, apply=True) == 0
    assert len([row for row in service.store.read("admin_logs") if row["action"] == "PDF_LOAN_MIGRATED"]) == 1


def test_numeric_military_id_and_true_active_string_authenticate(tmp_path):
    store = CsvStore(tmp_path / "data")
    service = BookRentalService(store, clock=lambda: NOW)
    user = service.register_user("엄준식", "333", "password333", "password333")
    rows = store.read("users")
    rows[0]["active"] = "True"
    store.write("users", rows)

    result = service.authenticate(333, "password333")

    assert result.succeeded is True
    assert result.user == {
        "id": user["id"], "name": "엄준식", "military_id": "333", "role": "USER",
        "active": "true", "created_at": user["created_at"], "updated_at": user["updated_at"],
    }


def test_authenticate_reads_users_from_bookbridge_data_dir(tmp_path, monkeypatch):
    configured = tmp_path / "production-data"
    monkeypatch.setenv("BOOKBRIDGE_DATA_DIR", str(configured))
    writer = BookRentalService(CsvStore())
    writer.register_user("운영 사용자", "333", "password333", "password333")

    reader = BookRentalService(CsvStore())
    result = reader.authenticate("333", "password333")

    assert reader.store.path("users") == configured.resolve() / "users.csv"
    assert result.succeeded is True
    assert result.user["name"] == "운영 사용자"
