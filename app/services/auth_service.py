from sqlalchemy.orm import Session

from app import models
from app.utils.hashing import verify_password
from app.utils.token import create_access_token


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return None, None

    # Optional MFA enforcement
    if user.mfa_enabled:
        # Token returned, but second step required on frontend
        token = create_access_token({"sub": str(user.id), "mfa": False})
        return user, token

    token = create_access_token({"sub": str(user.id), "mfa": True})
    return user, token