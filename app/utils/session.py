import os

from fastapi import Request, Response
from itsdangerous import URLSafeSerializer

SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY")
session_serializer = URLSafeSerializer(SESSION_SECRET_KEY, salt="session")

SESSION_COOKIE_NAME = "pixelforge_session"


def create_session_token(user_id: int) -> str:
    return session_serializer.dumps({"user_id": user_id})


def get_session_user(request: Request):
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_cookie:
        return None
    try:
        session_data = session_serializer.loads(session_cookie)
        return session_data.get("user_id")
    except Exception:
        return None


def set_session_cookie(response: Response, user_id: int):
    token = create_session_token(user_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=3600 * 24,  # 1 day
        samesite="lax",
        secure=False,  # change to True with HTTPS
    )


def clear_session_cookie(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME)