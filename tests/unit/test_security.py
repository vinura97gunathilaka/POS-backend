"""
tests/unit/test_security.py
----------------------------
Unit tests for app.core.security (password hashing and JWT).
These tests have NO database or HTTP dependencies.
"""

import pytest
from datetime import timedelta
from jose import jwt

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    ALGORITHM,
)
from app.core.config import settings


# --------------------------------------------------------------------------- #
#  Password hashing                                                            #
# --------------------------------------------------------------------------- #

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = get_password_hash("mypassword123")
        assert hashed != "mypassword123"

    def test_verify_correct_password(self):
        hashed = get_password_hash("correct_password")
        assert verify_password("correct_password", hashed) is True

    def test_reject_wrong_password(self):
        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hashes_are_unique(self):
        """bcrypt uses random salt — two hashes of the same password differ."""
        h1 = get_password_hash("same_password")
        h2 = get_password_hash("same_password")
        assert h1 != h2


# --------------------------------------------------------------------------- #
#  JWT token generation                                                        #
# --------------------------------------------------------------------------- #

class TestJWTTokens:
    def test_access_token_contains_subject(self):
        token = create_access_token(subject=42)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_refresh_token_type(self):
        token = create_refresh_token(subject=99)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["type"] == "refresh"

    def test_access_token_custom_expiry(self):
        token = create_access_token(subject=1, expires_delta=timedelta(minutes=5))
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload

    def test_access_and_refresh_are_different(self):
        access = create_access_token(subject=7)
        refresh = create_refresh_token(subject=7)
        assert access != refresh
