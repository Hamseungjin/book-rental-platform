from __future__ import annotations

from datetime import datetime, timezone

import pytest

from book_rental.admin_data import AdminDataService
from book_rental.auth import verify_password
from book_rental.errors import AuthorizationError, ValidationError
from book_rental.service import BookRentalService
from book_rental.store import SCHEMAS, CsvStore

NOW = datetime(2026, 6, 13, 10, 30, tzinfo=timezone.utc)


@pytest.fixture
def managed(tmp_path):
    store = CsvStore(tmp_path / "data")
    service = BookRentalService(store, clock=lambda: NOW)
    admin, _ = service.create_admin("관리자", "admin", "admin1234")
    user = service.register_user("회원", "member", "member123", "member123")
    return AdminDataService(store, clock=lambda: NOW), store, admin, user


def book_row(row_id="1", title="책", quantity="2"):
    return dict(zip(SCHEMAS["books"], [
        row_id, "2", title, "저자", "분류", "설명", "PHYSICAL_BOOK", quantity, quantity,
        "14", "APPROVED", "", "", "", NOW.isoformat(), NOW.isoformat(),
    ]))


def test_normal_user_cannot_access_admin_data(managed):
    data, _, _, user = managed
    with pytest.raises(AuthorizationError, match="권한이 없습니다"):
        data.read_table(user, "users")


def test_admin_can_read_users_without_password_hash_disclosure(managed):
    data, _, admin, _ = managed
    rows = data.read_table(admin, "users")
    assert rows
    assert all(row["password_hash"] == "••••••••" for row in rows)


def test_admin_can_add_update_and_delete_book_rows(managed):
    data, store, admin, _ = managed
    data.save_table(admin, "books", [book_row()])
    assert store.read("books")[0]["title"] == "책"
    updated = book_row(title="수정된 책")
    data.save_table(admin, "books", [updated])
    assert store.read("books")[0]["title"] == "수정된 책"
    data.save_table(admin, "books", [])
    assert store.read("books") == []
    assert len(store.read("admin_logs")) == 3


def test_save_creates_timestamped_backup(managed):
    data, store, admin, _ = managed
    backup = data.save_table(admin, "books", [book_row()])
    assert backup.parent == store.data_dir / "backups"
    assert backup.name.startswith("books_20260613_103000_")
    assert backup.read_text(encoding="utf-8").startswith("id,lender_id,title")


def test_invalid_book_quantity_is_not_saved(managed):
    data, store, admin, _ = managed
    with pytest.raises(ValidationError, match="음수"):
        data.save_table(admin, "books", [book_row(quantity="-1")])
    assert store.read("books") == []


def test_duplicate_military_id_is_not_saved(managed):
    data, _, admin, _ = managed
    rows = data.read_table(admin, "users")
    rows[1]["military_id"] = rows[0]["military_id"]
    with pytest.raises(ValidationError, match="military_id"):
        data.save_table(admin, "users", rows)


def test_password_reset_hashes_plaintext(managed):
    data, store, admin, user = managed
    data.reset_password(admin, int(user["id"]), "new-password")
    saved = next(row for row in store.read("users") if row["id"] == user["id"])
    assert saved["password_hash"] != "new-password"
    assert verify_password("new-password", saved["password_hash"])


def test_plaintext_password_hash_column_is_rejected(managed):
    data, _, admin, _ = managed
    rows = data.read_table(admin, "users")
    rows[0]["password_hash"] = "plain-password"
    with pytest.raises(ValidationError, match="평문"):
        data.save_table(admin, "users", rows)


def test_admin_adds_user_with_hashed_password(managed):
    data, store, admin, _ = managed
    created = data.create_user(admin, "새 회원", "new-member", "safe-password")
    saved = next(row for row in store.read("users") if row["id"] == created["id"])
    assert saved["password_hash"] != "safe-password"
    assert verify_password("safe-password", saved["password_hash"])


def test_admin_data_accepts_boolean_active_from_login_session(managed, monkeypatch):
    data, _, admin, _ = managed
    session_admin = {**admin, "active": True}

    def legacy_string_only_is_active(value):
        return value.lower() == "true"

    monkeypatch.setattr(CsvStore, "is_active", staticmethod(legacy_string_only_is_active))

    rows = data.read_table(session_admin, "users")

    assert rows


@pytest.mark.parametrize("active", [False, "false", "False", "0", "off", None])
def test_admin_data_rejects_inactive_boolean_and_string_values(managed, active):
    data, _, admin, _ = managed
    with pytest.raises(AuthorizationError, match="권한이 없습니다"):
        data.read_table({**admin, "active": active}, "users")


def test_admin_data_normalizes_role_for_session_actor(managed):
    data, _, admin, _ = managed
    assert data.read_table({**admin, "role": " admin ", "active": True}, "users")
