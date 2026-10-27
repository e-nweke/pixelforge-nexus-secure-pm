from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import MFACode, Token
from app.services import auth_service
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user, token = auth_service.authenticate_user(
        db, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if user.mfa_enabled:
        return {"access_token": token, "token_type": "bearer", "mfa_required": True}

    return {"access_token": token, "token_type": "bearer"}


@router.post("/mfa/verify")
def verify_mfa(
    payload: MFACode,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not auth_service.verify_totp(user, payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code"
        )
    token = auth_service.create_access_token({"sub": str(user.id), "mfa": True})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/mfa/setup")
def setup_mfa(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = auth_service.enable_mfa_for_user(user, db)
    uri = f"otpauth://totp/PixelForgeNexus:{user.username}?secret={secret}&issuer=PixelForgeNexus"
    return {"secret": secret, "uri": uri}