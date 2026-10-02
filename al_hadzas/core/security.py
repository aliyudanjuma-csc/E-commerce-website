"""
core/security.py
------------------
OWASP-aligned security helpers used across the app. Each function is
annotated with the OWASP Top 10 (2021) category it addresses.

    A01 Broken Access Control     -> require_role()
    A02 Cryptographic Failures    -> hash_password()/verify_password() (salted PBKDF2-SHA256,
                                      never store plaintext passwords)
    A03 Injection                 -> sanitize_text(), validate_email()
    A04 Insecure Design           -> LoginRateLimiter (account lockout after repeated failures)
    A05 Security Misconfiguration -> SecurityConfig (central, explicit settings; no
                                      framework defaults silently trusted)
    A07 Identification & Auth
        Failures                  -> generate_session_token(), session expiry
    A08 Software & Data Integrity -> AntivirusScanner (upload validation before a file
                                      is accepted into the catalogue)
    A09 Security Logging &
        Monitoring Failures       -> DataStore.log_action() (see data_store.py), called
                                      from every sensitive action in the UI layer
    A10 SSRF                      -> not directly applicable (no server-side fetch of
                                      user-supplied URLs in this MVP); noted for future work.

All complexity here is O(1) or O(n) in the size of the single input being
checked (a password, a filename, a piece of text) - never O(n) over the
whole user base, so these checks stay cheap regardless of platform size.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import time
from dataclasses import dataclass


# ---------------------------------------------------------------------
# A05 - Security configuration, defined explicitly rather than relying
# on defaults.
# ---------------------------------------------------------------------
class SecurityConfig:
    PBKDF2_ITERATIONS = 260_000          # OWASP-recommended minimum for PBKDF2-HMAC-SHA256
    SESSION_TTL_SECONDS = 60 * 60        # 1 hour session expiry
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_SECONDS = 5 * 60             # 5 minute lockout after repeated failures
    ALLOWED_UPLOAD_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    MAX_UPLOAD_BYTES = 5 * 1024 * 1024   # 5MB
    MIN_PASSWORD_LENGTH = 8


# ---------------------------------------------------------------------
# A02 - Cryptographic failures: never store or compare plaintext passwords
# ---------------------------------------------------------------------
def hash_password(plain_password: str, salt: str | None = None) -> tuple[str, str]:
    """Return (hash_hex, salt_hex). Uses PBKDF2-HMAC-SHA256 with a random salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        bytes.fromhex(salt),
        SecurityConfig.PBKDF2_ITERATIONS,
    )
    return dk.hex(), salt


def verify_password(plain_password: str, stored_hash: str, salt: str) -> bool:
    candidate, _ = hash_password(plain_password, salt)
    # constant-time comparison to avoid timing attacks
    return hmac.compare_digest(candidate, stored_hash)


def password_strength_errors(password: str) -> list[str]:
    errors = []
    if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain an uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain a lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain a digit.")
    return errors


# ---------------------------------------------------------------------
# A03 - Injection / input validation. Since this MVP uses an in-memory
# store (no raw SQL), the risk here is really XSS-style payloads
# leaking into rendered text and malformed data corrupting records --
# both are neutralised by strict allow-list validation below.
# ---------------------------------------------------------------------
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_UNSAFE_CHARS_RE = re.compile(r"[<>{}$`]")


def validate_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email.strip()))


def sanitize_text(text: str, max_len: int = 2000) -> str:
    """Strip characters commonly used in script/template injection and
    hard-cap length to prevent memory-exhaustion style abuse."""
    cleaned = _UNSAFE_CHARS_RE.sub("", text).strip()
    return cleaned[:max_len]


def validate_price(value: str) -> float | None:
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    if price < 0 or price > 1_000_000:
        return None
    return round(price, 2)


# ---------------------------------------------------------------------
# A04 - Insecure design: brute-force login protection
# ---------------------------------------------------------------------
class LoginRateLimiter:
    """Per-user lockout after repeated failed attempts. O(1) per check."""

    @staticmethod
    def is_locked(user) -> bool:
        return time.time() < getattr(user, "locked_until", 0)

    @staticmethod
    def register_failure(user) -> None:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
            user.locked_until = time.time() + SecurityConfig.LOCKOUT_SECONDS
            user.failed_login_attempts = 0

    @staticmethod
    def register_success(user) -> None:
        user.failed_login_attempts = 0
        user.locked_until = 0.0


# ---------------------------------------------------------------------
# A07 - Session/auth: opaque, unguessable session tokens with expiry
# ---------------------------------------------------------------------
@dataclass
class Session:
    token: str
    user_id: str
    role: str
    expires_at: float


_active_sessions: dict[str, Session] = {}   # token -> Session, O(1) lookups


def generate_session_token(user_id: str, role: str) -> Session:
    token = secrets.token_urlsafe(32)
    session = Session(token=token, user_id=user_id, role=role,
                       expires_at=time.time() + SecurityConfig.SESSION_TTL_SECONDS)
    _active_sessions[token] = session
    return session


def get_session(token: str) -> Session | None:
    session = _active_sessions.get(token)
    if session is None:
        return None
    if time.time() > session.expires_at:
        _active_sessions.pop(token, None)
        return None
    return session


def invalidate_session(token: str) -> None:
    _active_sessions.pop(token, None)


# ---------------------------------------------------------------------
# A01 - Broken access control: centralised role check used before every
# sensitive UI action / route render.
# ---------------------------------------------------------------------
def require_role(session: Session | None, allowed_roles: set[str]) -> bool:
    return session is not None and session.role in allowed_roles


# ---------------------------------------------------------------------
# A08 - Software & data integrity: simulated "antivirus" scanner for
# vendor uploads (product images). No external engine is available in
# this coursework sandbox, so the scanner combines:
#   1. Extension allow-listing
#   2. File size limits
#   3. A signature/hash check against a small blocklist of known
#      EICAR-style test signatures (the same technique real AV smoke
#      tests use) so the control is demonstrably testable.
# This models the *behaviour* of an antivirus gate (reject before the
# file ever reaches storage) even though it is not a full malware engine.
# ---------------------------------------------------------------------
EICAR_TEST_SIGNATURE = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

_BLOCKED_HASH_PREFIXES = {
    hashlib.sha256(EICAR_TEST_SIGNATURE.encode()).hexdigest(),
}


@dataclass
class ScanResult:
    passed: bool
    reason: str = ""


class AntivirusScanner:
    """Simulated upload scanner. O(n) in the size of the single file
    being scanned (n = file bytes) -- independent of catalogue size."""

    @staticmethod
    def scan(filename: str, content: bytes) -> ScanResult:
        ext = os.path.splitext(filename.lower())[1]
        if ext not in SecurityConfig.ALLOWED_UPLOAD_EXTENSIONS:
            return ScanResult(False, f"File type '{ext}' is not allowed.")

        if len(content) == 0:
            return ScanResult(False, "Empty file rejected.")

        if len(content) > SecurityConfig.MAX_UPLOAD_BYTES:
            return ScanResult(False, "File exceeds the 5MB upload limit.")

        digest = hashlib.sha256(content).hexdigest()
        if digest in _BLOCKED_HASH_PREFIXES:
            return ScanResult(False, "File matched a known malicious signature.")

        # Reject files that embed the EICAR test string even if the hash
        # differs (e.g. re-saved/re-encoded), by scanning raw bytes once - O(n).
        if EICAR_TEST_SIGNATURE.encode() in content:
            return ScanResult(False, "File contains a known test-malware signature.")

        return ScanResult(True, "Clean.")
