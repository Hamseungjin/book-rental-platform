from datetime import datetime, timezone

import pytest

from book_rental.errors import ValidationError
from book_rental.service import BookRentalService
from book_rental.store import CsvStore

NOW = datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def service(tmp_path):
    return BookRentalService(CsvStore(tmp_path / "data"), clock=lambda: NOW)


def create_approved_book(service, quantity=2):
    book = service.create_book(
        2,
        title="도메인 주도 설계",
        author="Eric Evans",
        category="소프트웨어",
        description="DDD 참고서",
        book_format="PHYSICAL_BOOK",
        total_quantity=quantity,
        default_loan_days=14,
    )
    service.approve_book(1, int(book["id"]))
    return book


def test_complete_loan_lifecycle_restores_inventory(service):
    book = create_approved_book(service)
    request = service.create_borrow_request(3, int(book["id"]), 1)

    loan = service.approve_request(1, int(request["id"]))

    assert loan["status"] == "LOANED"
    assert service.approved_books()[0]["available_quantity"] == "1"
    assert service.borrower_requests(3)[0]["status"] == "APPROVED"

    service.return_book(3, int(loan["id"]))

    assert service.loans(3)[0]["status"] == "RETURNED"
    assert service.approved_books()[0]["available_quantity"] == "2"


def test_second_approval_fails_without_partial_csv_updates(service):
    second_borrower = service.create_user("두 번째 대여자", "borrower2@example.com", ["BORROWER"])
    book = create_approved_book(service, quantity=1)
    first = service.create_borrow_request(3, int(book["id"]), 1)
    second = service.create_borrow_request(int(second_borrower["id"]), int(book["id"]), 1)
    service.approve_request(1, int(first["id"]))

    with pytest.raises(ValidationError, match="수량이 부족"):
        service.approve_request(1, int(second["id"]))

    assert service.approved_books()[0]["available_quantity"] == "0"
    requests = service.all_requests(1)
    failed_request = next(row for row in requests if row["id"] == second["id"])
    assert failed_request["status"] == "REQUESTED"
    assert len(service.loans(1, admin=True)) == 1


def test_pdf_requires_a_pdf_upload(service):
    with pytest.raises(ValidationError, match="PDF 파일을 첨부"):
        service.create_book(
            2,
            title="전자책",
            author="작가",
            category="에세이",
            description="",
            book_format="PDF",
            total_quantity=1,
            default_loan_days=7,
        )


def test_overdue_status_is_synchronized_when_loans_are_read(tmp_path):
    approval_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    current_time = [approval_time]
    service = BookRentalService(CsvStore(tmp_path / "data"), clock=lambda: current_time[0])
    book = create_approved_book(service)
    request = service.create_borrow_request(3, int(book["id"]), 1)
    service.approve_request(1, int(request["id"]))
    current_time[0] = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)

    assert service.loans(3)[0]["status"] == "OVERDUE"
