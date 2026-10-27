import os
from datetime import datetime, timedelta

from fastapi import HTTPException
import pyotp
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.models import User

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str, credentials_exception: HTTPException):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        mfa_verified: bool = payload.get("mfa", False)
        if user_id is None or not mfa_verified:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return user_id


def verify_totp(user: User, code: str):
    if not user.mfa_secret:
        return False
    totp = pyotp.TOTP(user.mfa_secret)
    return totp.verify(code)


def enable_mfa_for_user(user: User, db: Session):
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    user.mfa_enabled = True
    db.commit()
    db.refresh(user)
    return secret