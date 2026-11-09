"""Password hashing, signed session tokens, and login rate-limiting for Clacktivity."""

import hashlib
import hmac
import secrets
import time
from src.database import Database

PBKDF2_ITERATIONS = 600_000
MIN_PASSWORD_LENGTH = 4
DEFAULT_EXPIRATION_HOURS = 2
MAX_FAILED_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SEC = 60.0


class AuthManager:
    """Manages master password storage, session token verification, and login rate limits."""

    COOKIE_NAME = "clacktivity_session"

    def __init__(self, db: Database) -> None:
        self.db = db
        self._failed_attempts: dict[str, list[float]] = {}

    def _ensure_secret_key(self) -> str:
        secret = self.db.get_setting("auth_secret_key")
        if not secret:
            secret = secrets.token_hex(32)
            self.db.set_setting("auth_secret_key", secret)
        return secret

    def _get_session_version(self) -> int:
        raw = self.db.get_setting("auth_session_version", "1")
        try:
            return int(raw or "1")
        except ValueError:
            return 1

    def _bump_session_version(self) -> int:
        next_ver = self._get_session_version() + 1
        self.db.set_setting("auth_session_version", str(next_ver))
        return next_ver

    def is_password_enabled(self) -> bool:
        """Return True if a master password hash is currently configured."""
        stored = self.db.get_setting("auth_password_hash")
        return bool(stored and stored.strip())

    def get_expiration_hours(self) -> int:
        """Return configured session token expiration in hours (default 2)."""
        raw = self.db.get_setting("auth_token_expiration_hours", str(DEFAULT_EXPIRATION_HOURS))
        try:
            val = int(raw or DEFAULT_EXPIRATION_HOURS)
            return max(1, min(val, 720))
        except ValueError:
            return DEFAULT_EXPIRATION_HOURS

    def set_expiration_hours(self, hours: int) -> int:
        """Persist clamped session expiration hours (1..720)."""
        clamped = max(1, min(int(hours), 720))
        self.db.set_setting("auth_token_expiration_hours", str(clamped))
        return clamped

    def set_password(self, new_password: str, expiration_hours: int | None = None) -> None:
        """Hash and store a new master password and invalidate prior sessions."""
        if len(new_password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            new_password.encode("utf-8"),
            salt.encode("utf-8"),
            PBKDF2_ITERATIONS,
        ).hex()
        encoded = f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"
        self._ensure_secret_key()
        self.db.set_setting("auth_password_hash", encoded)
        if expiration_hours is not None:
            self.set_expiration_hours(expiration_hours)
        self._bump_session_version()

    def clear_password(self) -> None:
        """Disable password lock and invalidate existing sessions."""
        self.db.delete_setting("auth_password_hash")
        self._bump_session_version()

    def verify_password(self, password: str) -> bool:
        """Verify candidate password against stored PBKDF2-HMAC-SHA256 hash."""
        stored = self.db.get_setting("auth_password_hash")
        if not stored:
            return True
        parts = stored.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        try:
            iterations = int(parts[1])
        except ValueError:
            return False
        salt, expected_hex = parts[2], parts[3]
        candidate_hex = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()
        return hmac.compare_digest(candidate_hex, expected_hex)

    def create_session_token(self) -> tuple[str, int]:
        """Create a signed session token and return (token, max_age_seconds)."""
        secret = self._ensure_secret_key()
        version = self._get_session_version()
        max_age = self.get_expiration_hours() * 3600
        issued_at = int(time.time())
        expires_at = issued_at + max_age
        payload = f"{issued_at}.{expires_at}.{version}"
        sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{payload}.{sig}", max_age

    def verify_session_token(self, token: str | None) -> bool:
        """Return True if password lock is disabled or if the signed session token is valid."""
        if not self.is_password_enabled():
            return True
        if not token or not isinstance(token, str):
            return False
        parts = token.split(".")
        if len(parts) != 4:
            return False
        issued_str, expires_str, ver_str, sig = parts
        try:
            expires_at = int(expires_str)
            token_ver = int(ver_str)
        except ValueError:
            return False
        if time.time() >= expires_at:
            return False
        if token_ver != self._get_session_version():
            return False
        secret = self._ensure_secret_key()
        payload = f"{issued_str}.{expires_str}.{ver_str}"
        expected_sig = hmac.new(
            secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(sig, expected_sig)

    def check_rate_limit(self, client_key: str = "local") -> bool:
        """Return True if client_key is allowed to attempt login, False if rate-limited."""
        now = time.time()
        cutoff = now - RATE_LIMIT_WINDOW_SEC
        attempts = [t for t in self._failed_attempts.get(client_key, []) if t > cutoff]
        self._failed_attempts[client_key] = attempts
        return len(attempts) < MAX_FAILED_ATTEMPTS

    def record_failed_attempt(self, client_key: str = "local") -> None:
        """Record a failed login timestamp for client_key."""
        now = time.time()
        cutoff = now - RATE_LIMIT_WINDOW_SEC
        attempts = [t for t in self._failed_attempts.get(client_key, []) if t > cutoff]
        attempts.append(now)
        self._failed_attempts[client_key] = attempts

    def clear_failed_attempts(self, client_key: str = "local") -> None:
        """Clear recorded failed login attempts for client_key."""
        self._failed_attempts.pop(client_key, None)
