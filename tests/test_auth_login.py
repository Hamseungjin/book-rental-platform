from __future__ import annotations

import logging

import pytest

from book_rental.auth import PasswordHashError, hash_password, verify_password
from book_rental.login import attempt_login
from book_rental.service import BookRentalService
from book_rental.sessions import SessionService
from book_rental.store import CsvStore


def test_hash_password_round_trip_and_wrong_password():
    encoded = hash_password("correct-password")
    assert verify_password("correct-password", encoded) is True
    assert verify_password("wrong-password", encoded) is False


def test_malformed_password_hash_is_distinct_from_wrong_password():
    with pytest.raises(PasswordHashError, match="필드 수"):
        verify_password("password", "not-a-valid-hash")


def test_session_creation_failure_is_logged_but_authentication_succeeds(tmp_path, caplog, monkeypatch):
    store = CsvStore(tmp_path / "data")
    service = BookRentalService(store)
    service.register_user("회원", "333", "password333", "password333")
    sessions = SessionService(store)

    def fail_create(user):
        raise PermissionError("sessions.csv permission denied")

    monkeypatch.setattr(sessions, "create", fail_create)
    logger = logging.getLogger("test.login")
    with caplog.at_level(logging.ERROR):
        attempt = attempt_login(service, sessions, "333", "password333", logger)

    assert attempt.result.succeeded is True
    assert attempt.token is None
    assert attempt.session_error is True
    assert "persistent session creation failed" in caplog.text
    assert "PermissionError" in caplog.text


def test_production_style_urlsafe_base64_hash_format_is_accepted():
    encoded = "pbkdf2_sha256$600000$Qd9pmg6TdfizwZjGPAxUvg==$04dtKCXx8SZGDYei2Z6OB_x_KpSwTg9_YjcDdyHJ28k="
    from book_rental.auth import is_password_hash_valid
    assert is_password_hash_valid(encoded) is True
