"""
Authentication utilities for Agent API.

Provides password hashing with bcrypt and cryptographic UID generation.
"""

from passlib.context import CryptContext
import secrets


# Password hashing context using bcrypt
# 12 rounds = 2^12 iterations (good balance of security vs performance)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash (max 72 bytes for bcrypt)

    Returns:
        Hashed password string (includes salt)

    Raises:
        ValueError: If password exceeds 72 bytes

    Example:
        >>> hashed = hash_password("MyPassword123!")
        >>> len(hashed)  # Bcrypt hashes are 60 characters
        60
    """
    # Bcrypt has a 72-byte limit, but we enforce 8-12 characters at API level
    # This is a safety check to ensure no encoding issues
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise ValueError(f"Password is {len(password_bytes)} bytes, bcrypt limit is 72 bytes")

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password to check against

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("MyPassword123!")
        >>> verify_password("MyPassword123!", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_uid() -> str:
    """
    Generate a cryptographically secure 12-character UID.

    Returns:
        12-character alphanumeric string (URL-safe)

    Example:
        >>> uid = generate_uid()
        >>> len(uid)
        12
        >>> uid.isalnum() or '-' in uid or '_' in uid
        True

    Notes:
        - Uses secrets module for cryptographic randomness
        - URL-safe base64 encoding (A-Z, a-z, 0-9, -, _)
        - Collision probability is extremely low
    """
    return secrets.token_urlsafe(9)[:12]
