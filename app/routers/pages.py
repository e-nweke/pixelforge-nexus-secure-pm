import pyotp
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, User, UserRole
from app.utils.dependencies import authenticate_user
from app.utils.hashing import hash_password
from app.utils.session import clear_session_cookie, get_session_user, set_session_cookie

router = APIRouter(tags=["Pages"])

# Set up Jinja2 templates folder
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home_page(
    request: Request,
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).get(user_id) if user_id else None
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).get(user_id) if user_id else None
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "user": user})


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    mfa_token: str = Form(None),
    db: Session = Depends(get_db),
):
    from app.utils.token import verify_totp  # import here

    user = authenticate_user(username, password, db)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # If MFA is enabled, verify the code
    if user.mfa_enabled:
        if not mfa_token or not verify_totp(user, mfa_token):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Invalid or missing MFA code"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    set_session_cookie(response, user.id)
    return response


@router.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    clear_session_cookie(response)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user: User = db.query(User).get(user_id) if user_id else None
    if not user:
        return RedirectResponse(url="/login")

    context = {"request": request, "user": user}

    if user.role == UserRole.Admin:
        context["projects"] = db.query(Project).all()
    elif user.role == UserRole.ProjectLead:
        # Use the relationship to get projects led by this user
        context["projects"] = db.query(Project).filter(Project.lead_id == user.id).all()
    elif user.role == UserRole.Developer:
        # Use assignments relationship to get assigned projects
        projects = [assignment.project for assignment in user.assignments]
        context["projects"] = projects

    return templates.TemplateResponse("dashboard.html", context)


@router.get("/account", response_class=HTMLResponse)
def account_page(
    request: Request,
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user: User = db.query(User).get(user_id) if user_id else None
    if not user:
        return RedirectResponse(url="/login")

       # MFA Setup Key (no QR code)
    mfa_key = None
    if user.mfa_enabled:
        if not user.mfa_secret:
            secret = pyotp.random_base32()
            user.mfa_secret = secret
            db.commit()
        mfa_key = user.mfa_secret  # Show secret directly

    return templates.TemplateResponse(
        "account.html",
        {
            "request": request,
            "user": user,
            "mfa_key": mfa_key
        },
    )



@router.post("/account")
def update_password(
    request: Request,
    new_password: str = Form(...),
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).get(user_id) if user_id else None
    if not user:
        return RedirectResponse(url="/login")

    user.password_hash = hash_password(new_password)
    db.commit()
    return templates.TemplateResponse(
        "account.html",
        {"request": request, "user": user, "success": "Password updated successfully."},
        status_code=status.HTTP_200_OK,
    )
@router.post("/account/enable-mfa")
def enable_mfa(
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user: User = db.query(User).get(user_id) if user_id else None
    if not user:
        return RedirectResponse(url="/login")

    if not user.mfa_enabled:
        import pyotp
        secret = pyotp.random_base32()
        user.mfa_enabled = True
        user.mfa_secret = secret
        db.commit()

    return RedirectResponse(url="/account", status_code=status.HTTP_302_FOUND)
