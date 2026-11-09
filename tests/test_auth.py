import time
import pytest
from pathlib import Path
from src.database import Database
from src.auth import AuthManager


def test_auth_default_unlocked_and_password_lifecycle(tmp_path: Path):
    db = Database(tmp_path / "auth.db")
    db.init_db()
    auth = AuthManager(db)

    assert auth.is_password_enabled() is False
    assert auth.get_expiration_hours() == 2
    assert auth.verify_session_token(None) is True

    with pytest.raises(ValueError, match="at least 4 characters"):
        auth.set_password("123")

    auth.set_password("mysecret", expiration_hours=12)
    assert auth.is_password_enabled() is True
    assert auth.get_expiration_hours() == 12
    assert auth.verify_password("mysecret") is True
    assert auth.verify_password("wrongpass") is False
    assert auth.verify_session_token(None) is False

    token, max_age = auth.create_session_token()
    assert max_age == 12 * 3600
    assert auth.verify_session_token(token) is True
    assert auth.verify_session_token(token + "tampered") is False

    # Changing password increments session_version and invalidates old tokens
    auth.set_password("newsecret")
    assert auth.verify_session_token(token) is False
    new_token, _ = auth.create_session_token()
    assert auth.verify_session_token(new_token) is True

    # Clearing password disables lock
    auth.clear_password()
    assert auth.is_password_enabled() is False
    assert auth.verify_session_token(None) is True


def test_auth_token_expiration_and_rate_limit(tmp_path: Path, monkeypatch):
    db = Database(tmp_path / "rate.db")
    db.init_db()
    auth = AuthManager(db)
    auth.set_password("secret123", expiration_hours=1)

    now = 1700000000.0
    monkeypatch.setattr(time, "time", lambda: now)
    token, _ = auth.create_session_token()
    assert auth.verify_session_token(token) is True

    # Advance past 1 hour expiration
    monkeypatch.setattr(time, "time", lambda: now + 3601)
    assert auth.verify_session_token(token) is False

    # Rate limit: 5 failed attempts within 60 seconds blocks 6th check
    for _ in range(5):
        assert auth.check_rate_limit("127.0.0.1") is True
        auth.record_failed_attempt("127.0.0.1")

    assert auth.check_rate_limit("127.0.0.1") is False
    auth.clear_failed_attempts("127.0.0.1")
    assert auth.check_rate_limit("127.0.0.1") is True
