"""
Authentication utilities for parent login/registration.
"""
import logging
import warnings
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from core.config import settings

# Suppress bcrypt version warning from passlib (harmless compatibility issue)
warnings.filterwarnings('ignore', category=UserWarning, module='passlib.handlers.bcrypt')
# Also suppress at logging level
logging.getLogger('passlib.handlers.bcrypt').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Password length should already be validated by Pydantic, but double-check
    if len(password) > 8:
        raise ValueError("Password must be no more than 8 characters long")
    
    try:
        # Use bcrypt directly to avoid passlib initialization issues
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        # Log the actual error for debugging
        logger.error(f"Password hashing error: {e}", exc_info=True)
        error_msg = str(e).lower()
        # Only show "too long" message if that's actually the issue
        if "cannot be longer than 72 bytes" in error_msg or "too long" in error_msg:
            raise ValueError("Password is too long. Please use a password between 6 and 8 characters.")
        # For other errors, provide a generic message
        raise ValueError("Failed to process password. Please try a different password.")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}", exc_info=True)
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None

