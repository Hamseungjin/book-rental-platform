from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol


class AuthenticationService(Protocol):
    store: Any

    def authenticate(self, military_id: str, password: str) -> object: ...


class PersistentSessionService(Protocol):
    def create(self, user: dict[str, object]) -> str: ...


@dataclass(frozen=True)
class NormalizedLoginResult:
    """Stable login result independent of the deployed service module version."""

    status: str
    user: dict[str, object] | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "SUCCESS" and self.user is not None


@dataclass(frozen=True)
class LoginAttempt:
    result: NormalizedLoginResult
    token: str | None = None
    session_error: bool = False


def normalize_authentication_result(raw_result: object) -> NormalizedLoginResult:
    """Accept both legacy dict/``error`` results and the current result object."""
    if isinstance(raw_result, dict):
        return NormalizedLoginResult(status="SUCCESS", user=_public_user(raw_result))

    status = getattr(raw_result, "status", None) or getattr(raw_result, "error", None)
    user = getattr(raw_result, "user", None)
    if status == "SUCCESS" and isinstance(user, dict):
        return NormalizedLoginResult(status="SUCCESS", user=_public_user(user))
    if status in {"ACCOUNT_NOT_FOUND", "INVALID_PASSWORD", "ACCOUNT_INACTIVE"}:
        return NormalizedLoginResult(status=status)
    raise TypeError(f"지원하지 않는 authenticate 반환 형식입니다: {type(raw_result).__name__}")


def attempt_login(
    service: AuthenticationService,
    sessions: PersistentSessionService,
    military_id: str,
    password: str,
    logger: logging.Logger,
) -> LoginAttempt:
    """Authenticate first, then independently try to create a persistent session."""
    result = normalize_authentication_result(service.authenticate(military_id, password))
    if not result.succeeded:
        return LoginAttempt(result=result)
    try:
        token = sessions.create(result.user or {})
    except Exception:
        store = getattr(service, "store", None)
        data_dir = getattr(store, "data_dir", "unknown")
        try:
            sessions_path = store.path("sessions") if store is not None else "unknown"
        except Exception:
            sessions_path = "unknown"
        logger.exception(
            "Authentication succeeded but persistent session creation failed for user_id=%s data_dir=%s sessions_path=%s",
            (result.user or {}).get("id", "unknown"), data_dir, sessions_path,
        )
        return LoginAttempt(result=result, session_error=True)
    return LoginAttempt(result=result, token=token)


def _public_user(user: dict[str, object]) -> dict[str, object]:
    """Normalize the session-safe user shape used by Streamlit."""
    role = str(user.get("role") or "USER").strip().upper() or "USER"
    active_value = user.get("active", True)
    is_active = active_value if isinstance(active_value, bool) else str(active_value).strip().casefold() in {
        "true", "1", "yes", "y", "on",
    }
    return {
        "id": str(user.get("id", "")).strip(),
        "name": str(user.get("name", "")).strip(),
        "military_id": str(user.get("military_id", "")).strip(),
        "role": role,
        # Keep the public/session boundary compatible with legacy code that calls .lower().
        "active": "true" if is_active else "false",
        "created_at": str(user.get("created_at", "")),
        "updated_at": str(user.get("updated_at", "")),
    }
