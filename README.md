# PixelForge Nexus: Secure Project Management Portal

A role-based project management web app I built with FastAPI, designed from the ground up around secure development practices. I made this for the Secure Software Design & Development module.

> This is a university prototype for local use, not a production system. I've listed the known limitations as well.

## Features

- **Authentication:** bcrypt password hashing (passlib), signed HttpOnly session cookies
- **MFA:** TOTP (Google Authenticator compatible) using PyOTP, with QR-code setup
- **RBAC:** Admin, Project Lead and Developer roles enforced through FastAPI dependencies
- **Documents:** per-project uploads stored under UUID-based names with versioning
- **Validation:** Pydantic models and SQLAlchemy ORM (parameterised queries, so no raw SQL injection surface)
- **Architecture:** routers / services / utils kept separate rather than one big file

| Action | Admin | Project Lead | Developer |
|---|---|---|---|
| Create project | Yes | No | No |
| Assign developers | Yes | Yes | No |
| Upload documents | Yes | Yes | No |
| View assigned projects | Yes | Yes | Yes |
| Manage users | Yes | No | No |

## How I approached the security

I threat-modelled it with STRIDE and mapped the risks against the OWASP Top 10. Secrets (session and JWT keys) are loaded from environment variables, never hard-coded. Running OWASP ZAP and doing manual testing turned up missing cookie flags and an MFA validation bypass, I fixed the MFA issue by enforcing MFA claims directly in the tokens rather than just checking at login.

## Known limitations

I'd rather be upfront about what's not production-ready here:
- Session cookie `Secure` flag is off (needs HTTPS before any real deployment)
- CSRF tokens aren't implemented on every form yet
- No rate limiting or login lockout
- MFA setup key is shown on the account page
- SQLite and local hosting only, no automated dependency scanning

If I took this further, it would move to AWS hosting, PostgreSQL (RDS), HTTPS, and AWS Secrets Manager.

## Run locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your own random secrets in .env
python create_admin.py      # create the first Admin
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Tech stack

Python, FastAPI, SQLAlchemy, SQLite, Jinja2, passlib/bcrypt, PyOTP, python-jose, itsdangerous, OWASP ZAP
