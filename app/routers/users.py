from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserRole
from app.utils.hashing import hash_password
from app.utils.session import get_session_user

router = APIRouter(prefix="/users", tags=["Users"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def user_management_page(
    request: Request,
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user: User = db.query(User).get(user_id) if user_id else None
    if not user or user.role not in [UserRole.Admin]:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    users = db.query(User).all()
    return templates.TemplateResponse(
        "user_management.html", {"request": request, "user": user, "users": users}
    )


@router.post("/{user_id}/update-role")
def update_user_role(
    user_id: int,
    role: str = Form(...),
    current_user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    current_user: User = (
        db.query(User).get(current_user_id) if current_user_id else None
    )
    if not current_user or current_user.role not in [UserRole.Admin]:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    if role not in UserRole.__members__:
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    user.role = UserRole[role]
    db.commit()
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/register")
def register_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    current_user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    current_user: User = (
        db.query(User).get(current_user_id) if current_user_id else None
    )
    if not current_user or current_user.role not in [UserRole.Admin]:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    if role not in UserRole.__members__:
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    new_user = User(
        username=username, password_hash=hash_password(password), role=UserRole[role]
    )
    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{user_id}/delete")
def delete_user(
    user_id: int,
    current_user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    current_user: User = (
        db.query(User).get(current_user_id) if current_user_id else None
    )
    if not current_user or current_user.role not in [UserRole.Admin]:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    db.delete(user)
    db.commit()
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)