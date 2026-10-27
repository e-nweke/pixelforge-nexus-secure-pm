# PixelForge Nexus – Secure Project Management Portal

A role-based project management web app built with **FastAPI**, designed around secure development practices. Created for the Secure Software Design & Development module of my MSc Cybersecurity at Coventry University.

> This is a university prototype for local use, not a production system. Known limitations are listed honestly below.

## Features
- **Authentication:** bcrypt password hashing (passlib), signed HttpOnly session cookies
- **MFA:** TOTP (Google Authenticator compatible) using PyOTP, with QR-code setup
- **RBAC:** Admin, Project Lead and Developer roles enforced through FastAPI dependencies
- **Documents:** per-project uploads stored under UUID-based names with versioning
- **Validation:** Pydantic models and SQLAlchemy ORM (parameterised queries)
- **Architecture:** routers / services / utils separation

| Action | Admin | Project Lead | Developer |
|---|---|---|---|
| Create project | Yes | No | No |
| Assign developers | Yes | Yes | No |
| Upload documents | Yes | Yes | No |
| View assigned projects | Yes | Yes | Yes |
| Manage users | Yes | No | No |

## Security design
Threat modelled with **STRIDE** and mapped to **OWASP Top 10** risks. Secrets (session and JWT keys) are loaded from environment variables, never hard-coded. OWASP ZAP and manual testing found missing cookie flags and an MFA validation bypass; the MFA issue was fixed by enforcing MFA claims in tokens.

## Known limitations
- Session cookie `Secure` flag is off (needs HTTPS before real deployment)
- CSRF tokens are not implemented on all forms
- No rate limiting or login lockout
- MFA setup key is displayed in the account page
- SQLite and local hosting only; no automated dependency scanning

Planned: AWS hosting, PostgreSQL (RDS), HTTPS, AWS Secrets Manager.

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
