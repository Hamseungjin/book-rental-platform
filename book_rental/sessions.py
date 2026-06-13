from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

from .store import CsvStore

SESSION_MINUTES = 15


class SessionService:
    """Persistent, sliding 15-minute login sessions; only token hashes are stored."""

    def __init__(self, store: CsvStore, clock: Callable[[], datetime] | None = None) -> None:
        self.store = store
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def create(self, user: dict[str, str]) -> str:
        token = secrets.token_urlsafe(48)
        now = self.clock()
        with self.store.transaction():
            sessions = self.store.read("sessions")
            sessions.append({
                "token_hash": self._hash(token), "user_id": user["id"], "military_id": user["military_id"],
                "role": user["role"], "created_at": self._iso(now), "expires_at": self._iso(now + timedelta(minutes=SESSION_MINUTES)),
                "revoked_at": "", "last_seen_at": self._iso(now),
            })
            self.store.write("sessions", sessions)
        return token

    def restore(self, token: str) -> dict[str, str] | None:
        if not token:
            return None
        now = self.clock()
        with self.store.transaction():
            sessions = self.store.read("sessions")
            session = next((row for row in sessions if secrets.compare_digest(row["token_hash"], self._hash(token))), None)
            if session is None or session["revoked_at"] or datetime.fromisoformat(session["expires_at"]) <= now:
                return None
            users = self.store.read("users")
            user = next((row for row in users if row["id"] == session["user_id"]), None)
            if user is None or user["active"].lower() != "true" or user["role"] != session["role"]:
                return None
            session["last_seen_at"] = self._iso(now)
            session["expires_at"] = self._iso(now + timedelta(minutes=SESSION_MINUTES))
            self.store.write("sessions", sessions)
            return {key: value for key, value in user.items() if key != "password_hash"}

    def revoke(self, token: str) -> None:
        if not token:
            return
        with self.store.transaction():
            sessions = self.store.read("sessions")
            for session in sessions:
                if secrets.compare_digest(session["token_hash"], self._hash(token)) and not session["revoked_at"]:
                    session["revoked_at"] = self._iso(self.clock())
            self.store.write("sessions", sessions)

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _iso(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat(timespec="seconds")
