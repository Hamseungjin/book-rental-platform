from __future__ import annotations

import logging
from dataclasses import dataclass

from .service import BookRentalService, LoginResult
from .sessions import SessionService


@dataclass(frozen=True)
class LoginAttempt:
    result: LoginResult
    token: str | None = None
    session_error: bool = False


def attempt_login(
    service: BookRentalService,
    sessions: SessionService,
    military_id: str,
    password: str,
    logger: logging.Logger,
) -> LoginAttempt:
    """Authenticate first, then independently try to create a persistent session."""
    result = service.authenticate(military_id, password)
    if not result.succeeded:
        return LoginAttempt(result=result)
    try:
        token = sessions.create(result.user or {})
    except Exception:
        logger.exception(
            "Authentication succeeded but persistent session creation failed for user_id=%s data_dir=%s sessions_path=%s",
            (result.user or {}).get("id", "unknown"),
            service.store.data_dir,
            service.store.path("sessions"),
        )
        return LoginAttempt(result=result, session_error=True)
    return LoginAttempt(result=result, token=token)
