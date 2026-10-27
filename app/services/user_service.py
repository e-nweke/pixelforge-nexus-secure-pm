from sqlalchemy.orm import Session

from app import schemas
from app.utils.hashing import hash_password
from app import models


def get_all_users(db: Session):
    return db.query(models.User).all()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hash_password(user.password)
    db_user = models.User(
        username=user.username, password_hash=hashed_password, role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user