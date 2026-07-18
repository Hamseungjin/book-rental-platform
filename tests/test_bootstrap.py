from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from book_rental.auth import is_password_hash_valid, verify_password
from book_rental.bootstrap import bootstrap_dev_admin
from book_rental.service import BookRentalService
from book_rental.store import CsvStore


def make_service(tmp_path):
    return BookRentalService(CsvStore(tmp_path / "data"))


def dev_env(**overrides: str) -> dict[str, str]:
    env = {
        "APP_PROFILE": "dev",
        "DEV_BOOTSTRAP_ADMIN": "true",
        "DEV_ADMIN_MILITARY_ID": "dev-admin",
        "DEV_ADMIN_NAME": "개발 관리자",
        "DEV_ADMIN_PASSWORD": "local-only-password",
    }
    env.update(overrides)
    return env


def test_dev_bootstrap_creates_active_admin_with_hashed_authenticatable_password(tmp_path):
    service = make_service(tmp_path)

    result = bootstrap_dev_admin(service, environ=dev_env())

    users = service.store.read("users")
    assert result.created is True
    assert len(users) == 1
    assert users[0]["role"] == "ADMIN"
    assert users[0]["active"] == "true"
    assert users[0]["password_hash"] != "local-only-password"
    assert is_password_hash_valid(users[0]["password_hash"])
    assert service.authenticate("dev-admin", "local-only-password").succeeded is True


def test_dev_bootstrap_is_idempotent_for_same_settings(tmp_path):
    service = make_service(tmp_path)
    env = dev_env()

    first = bootstrap_dev_admin(service, environ=env)
    second = bootstrap_dev_admin(service, environ=env)

    assert first.status == "created"
    assert second.status == "exists"
    assert len(service.store.read("users")) == 1


def test_dev_bootstrap_existing_admin_does_not_change_password(tmp_path):
    service = make_service(tmp_path)
    service.create_admin("개발 관리자", "dev-admin", "old-password")
    old_hash = service.store.read("users")[0]["password_hash"]

    result = bootstrap_dev_admin(service, environ=dev_env(DEV_ADMIN_PASSWORD="new-password"))

    stored = service.store.read("users")[0]
    assert result.status == "exists"
    assert stored["password_hash"] == old_hash
    assert verify_password("old-password", stored["password_hash"]) is True
    assert verify_password("new-password", stored["password_hash"]) is False


def test_dev_bootstrap_existing_user_conflict_does_not_promote(tmp_path):
    service = make_service(tmp_path)
    service.register_user("일반 사용자", "dev-admin", "user-pass", "user-pass")

    result = bootstrap_dev_admin(service, environ=dev_env())

    stored = service.store.read("users")[0]
    assert result.status == "conflict_user"
    assert stored["role"] == "USER"
    assert verify_password("user-pass", stored["password_hash"]) is True


def test_prod_bootstrap_true_does_not_create_admin(tmp_path):
    service = make_service(tmp_path)

    result = bootstrap_dev_admin(service, environ=dev_env(APP_PROFILE="prod"))

    assert result.status == "disabled"
    assert service.store.read("users") == []


def test_unset_profile_does_not_create_admin(tmp_path):
    service = make_service(tmp_path)
    env = dev_env()
    env.pop("APP_PROFILE")

    result = bootstrap_dev_admin(service, environ=env)

    assert result.status == "disabled"
    assert service.store.read("users") == []


def test_unknown_profile_does_not_create_admin(tmp_path):
    service = make_service(tmp_path)

    result = bootstrap_dev_admin(service, environ=dev_env(APP_PROFILE="staging"))

    assert result.status == "disabled"
    assert service.store.read("users") == []


def test_bootstrap_false_does_not_create_admin_in_dev(tmp_path):
    service = make_service(tmp_path)

    result = bootstrap_dev_admin(service, environ=dev_env(DEV_BOOTSTRAP_ADMIN="false"))

    assert result.status == "disabled"
    assert service.store.read("users") == []


def test_missing_password_does_not_create_admin(tmp_path):
    service = make_service(tmp_path)
    env = dev_env()
    env.pop("DEV_ADMIN_PASSWORD")

    result = bootstrap_dev_admin(service, environ=env)

    assert result.status == "missing_config"
    assert result.missing == ("DEV_ADMIN_PASSWORD",)
    assert service.store.read("users") == []


def test_short_password_does_not_create_admin(tmp_path):
    service = make_service(tmp_path)

    result = bootstrap_dev_admin(service, environ=dev_env(DEV_ADMIN_PASSWORD="short"))

    assert result.status == "invalid_config"
    assert "8자 이상" in result.message
    assert service.store.read("users") == []


def test_missing_name_or_military_id_does_not_create_admin(tmp_path):
    for key in ("DEV_ADMIN_NAME", "DEV_ADMIN_MILITARY_ID"):
        service = make_service(tmp_path / key)
        env = dev_env()
        env[key] = " "

        result = bootstrap_dev_admin(service, environ=env)

        assert result.status == "missing_config"
        assert result.missing == (key,)
        assert service.store.read("users") == []


def test_profile_and_bootstrap_flag_are_normalized(tmp_path):
    service = make_service(tmp_path)

    result = bootstrap_dev_admin(
        service,
        environ=dev_env(APP_PROFILE=" Dev ", DEV_BOOTSTRAP_ADMIN=" TRUE "),
    )

    assert result.status == "created"
    assert len(service.store.read("users")) == 1


def test_bootstrap_logs_do_not_include_plaintext_password(tmp_path, caplog):
    service = make_service(tmp_path)
    logger = logging.getLogger("test.bootstrap")
    secret = "do-not-log-password"

    with caplog.at_level(logging.INFO, logger=logger.name):
        result = bootstrap_dev_admin(
            service,
            environ=dev_env(DEV_ADMIN_PASSWORD=secret),
            logger=logger,
        )

    assert result.status == "created"
    assert secret not in caplog.text
    assert service.store.read("users")[0]["password_hash"] not in caplog.text


def test_concurrent_bootstrap_creates_only_one_admin(tmp_path):
    data_dir = tmp_path / "data"
    env = dev_env()

    def run_once():
        return bootstrap_dev_admin(BookRentalService(CsvStore(data_dir)), environ=env).status

    with ThreadPoolExecutor(max_workers=4) as executor:
        statuses = list(executor.map(lambda _: run_once(), range(4)))

    users = CsvStore(data_dir).read("users")
    assert statuses.count("created") == 1
    assert statuses.count("exists") == 3
    assert len([row for row in users if row["military_id"] == "dev-admin"]) == 1
