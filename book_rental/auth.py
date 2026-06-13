from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000


class PasswordHashError(ValueError):
    """Raised when a stored password hash cannot be safely parsed."""


def hash_password(password: str) -> str:
    """Return a salted PBKDF2 password hash suitable for CSV storage."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return "$".join(
        (
            ALGORITHM,
            str(ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        )
    )


def parse_password_hash(encoded: str) -> tuple[int, bytes, bytes]:
    """Parse and validate ``pbkdf2_sha256$iterations$salt$digest`` hashes."""
    if not isinstance(encoded, str):
        raise PasswordHashError("password_hash가 문자열이 아닙니다.")
    parts = encoded.split("$")
    if len(parts) != 4:
        raise PasswordHashError("password_hash 필드 수가 올바르지 않습니다.")
    algorithm, iterations_value, salt_value, digest_value = parts
    if algorithm != ALGORITHM:
        raise PasswordHashError(f"지원하지 않는 password_hash 알고리즘입니다: {algorithm or '[비어 있음]'}")
    try:
        iterations = int(iterations_value)
    except ValueError as exc:
        raise PasswordHashError("password_hash 반복 횟수가 숫자가 아닙니다.") from exc
    if iterations < 1 or iterations > 10_000_000:
        raise PasswordHashError("password_hash 반복 횟수 범위가 올바르지 않습니다.")
    try:
        salt = base64.b64decode(salt_value.encode("ascii"), altchars=b"-_", validate=True)
        digest = base64.b64decode(digest_value.encode("ascii"), altchars=b"-_", validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
        raise PasswordHashError("password_hash의 Base64 값이 올바르지 않습니다.") from exc
    if not salt or len(digest) != hashlib.sha256().digest_size:
        raise PasswordHashError("password_hash의 salt 또는 digest 길이가 올바르지 않습니다.")
    return iterations, salt, digest


def is_password_hash_valid(encoded: str) -> bool:
    try:
        parse_password_hash(encoded)
        return True
    except PasswordHashError:
        return False


def verify_password(password: str, encoded: str) -> bool:
    """Verify a password, raising ``PasswordHashError`` for malformed stored data."""
    iterations, salt, expected = parse_password_hash(encoded)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)
