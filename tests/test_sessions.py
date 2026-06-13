from __future__ import annotations

from datetime import datetime, timedelta, timezone

from book_rental.service import BookRentalService
from book_rental.sessions import SessionService
from book_rental.store import CsvStore


def setup(tmp_path):
    current = [datetime(2026, 6, 13, 10, 0, tzinfo=timezone.utc)]
    store = CsvStore(tmp_path / "data")
    user = BookRentalService(store, clock=lambda: current[0]).register_user("회원", "member", "member123", "member123")
    sessions = SessionService(store, clock=lambda: current[0])
    return current, store, user, sessions


def test_login_creates_hashed_session_and_restores_within_15_minutes(tmp_path):
    current, store, user, sessions = setup(tmp_path)
    token = sessions.create(user)
    saved = store.read("sessions")[0]
    assert saved["token_hash"] != token
    assert len(saved["token_hash"]) == 64
    current[0] += timedelta(minutes=14)
    restored = sessions.restore(token)
    assert restored["id"] == user["id"]
    assert "password_hash" not in restored
    assert store.read("sessions")[0]["expires_at"] == (current[0] + timedelta(minutes=15)).isoformat(timespec="seconds")


def test_expired_session_cannot_restore_user(tmp_path):
    current, _, user, sessions = setup(tmp_path)
    token = sessions.create(user)
    current[0] += timedelta(minutes=16)
    assert sessions.restore(token) is None


def test_logout_revokes_token(tmp_path):
    _, store, user, sessions = setup(tmp_path)
    token = sessions.create(user)
    sessions.revoke(token)
    assert store.read("sessions")[0]["revoked_at"]
    assert sessions.restore(token) is None


def test_cookie_token_can_restore_after_new_service_instance(tmp_path):
    current, store, user, sessions = setup(tmp_path)
    cookie_token = sessions.create(user)
    refreshed_app_sessions = SessionService(CsvStore(store.data_dir), clock=lambda: current[0])
    assert refreshed_app_sessions.restore(cookie_token)["military_id"] == "member"
