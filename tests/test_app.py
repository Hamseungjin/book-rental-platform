from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from book_rental.service import BookRentalService
from book_rental.store import CsvStore

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def registration_app(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setenv("BOOKBRIDGE_DATA_DIR", str(data_dir))
    service = BookRentalService(CsvStore())
    user = service.register_user("등록 테스트", "test-member", "password1", "password1")

    app = AppTest.from_file(APP_PATH, default_timeout=10)
    app.session_state["user"] = user
    app.session_state["page"] = "책 등록"
    app.run()
    assert not app.exception
    return app, service


def complete_pdf_form(app: AppTest, *, include_file: bool) -> None:
    app.selectbox[0].select("PDF")
    app.text_input[0].set_value("테스트 PDF")
    app.text_input[1].set_value("테스트 저자")
    app.text_input[2].set_value("테스트")
    if include_file:
        app.file_uploader[0].set_value(("test.pdf", b"%PDF-1.4 test", "application/pdf"))
    app.button(key="FormSubmitter:book-form-승인 요청").click()
    app.run()


def test_pdf_uploader_is_enabled_on_initial_render(registration_app):
    app, _ = registration_app

    assert len(app.file_uploader) == 1
    assert app.file_uploader[0].disabled is False
    assert app.file_uploader[0].allowed_type == [".pdf"]


def test_pdf_submission_without_upload_shows_korean_error(registration_app):
    app, service = registration_app

    complete_pdf_form(app, include_file=False)

    assert [error.value for error in app.error] == ["PDF 파일을 업로드해주세요."]
    assert service.store.read("books") == []


def test_pdf_submission_succeeds_and_confirm_moves_to_lender_books(registration_app):
    app, service = registration_app

    complete_pdf_form(app, include_file=True)

    assert [message.value for message in app.success] == ["등록 신청이 완료되었습니다."]
    assert [message.value for message in app.toast] == ["등록 신청이 완료되었습니다."]
    assert app.session_state["book_registration_completed"] is True
    assert len(service.store.read("books")) == 1
    book = service.store.read("books")[0]
    assert book["status"] == "PENDING"
    assert book["file_name"] == "test.pdf"
    assert Path(book["file_path"]).read_bytes() == b"%PDF-1.4 test"

    app.button(key="book-registration-confirm").click()
    app.run()

    assert app.session_state["page"] == "내 등록 도서"
    assert "book_registration_completed" not in app.session_state
    assert "내 등록 도서" in [title.value for title in app.title]
    assert app.dataframe[0].value.iloc[0]["title"] == "테스트 PDF"
    assert len(service.store.read("books")) == 1


def test_login_flow_returns_app_compatible_user_and_creates_session(tmp_path, monkeypatch):
    data_dir = tmp_path / "login-data"
    monkeypatch.setenv("BOOKBRIDGE_DATA_DIR", str(data_dir))
    service = BookRentalService(CsvStore())
    service.register_user("엄준식", "333", "password333", "password333")
    app = AppTest.from_file(APP_PATH, default_timeout=10)
    app.session_state["page"] = "로그인"
    app.run()
    app.text_input[0].set_value("333")
    app.text_input[1].set_value("password333")
    app.button(key="FormSubmitter:login-form-로그인").click()
    app.run()

    assert not app.exception
    assert app.session_state["user"]["id"] == "1"
    assert app.session_state["user"]["active"] is True
    assert app.session_state["user"]["role"] == "USER"
    assert len(service.store.read("sessions")) == 1


def test_admin_data_page_accepts_boolean_active_session_user(tmp_path, monkeypatch):
    data_dir = tmp_path / "admin-data"
    monkeypatch.setenv("BOOKBRIDGE_DATA_DIR", str(data_dir))
    service = BookRentalService(CsvStore())
    admin, _ = service.create_admin("관리자", "admin", "admin1234")
    session_admin = {key: value for key, value in admin.items() if key != "password_hash"}
    session_admin["active"] = True

    app = AppTest.from_file(APP_PATH, default_timeout=10)
    app.session_state["user"] = session_admin
    app.session_state["page"] = "데이터 관리"
    app.run()

    assert not app.exception
    assert "데이터 관리" in [title.value for title in app.title]
    assert not [error.value for error in app.error if "권한이 없습니다" in error.value]
