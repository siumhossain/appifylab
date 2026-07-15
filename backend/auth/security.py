from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from common.config import get_settings
from common.response import CustomException

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def _signing_key(token_type: str) -> str:
    return f"{settings.JWT_SECRET}:{token_type}"


def _create_token(user_id: int, token_type: str, expires_delta: timedelta) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(
        payload, _signing_key(token_type), algorithm=settings.JWT_ALGORITHM
    )


def create_access_token(user_id: int) -> str:
    return _create_token(
        user_id, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        user_id, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str, expected_type: str) -> int:
    try:
        payload = jwt.decode(
            token, _signing_key(expected_type), algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise CustomException("Invalid or expired token", status_code=401)
    return int(payload["sub"])
