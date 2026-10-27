"""Create the first Admin user. Run once: python create_admin.py"""
import getpass

from dotenv import load_dotenv

load_dotenv()

from app.database import Base, SessionLocal, engine
from app.models import User, UserRole
from app.utils.hashing import hash_password

Base.metadata.create_all(bind=engine)
username = input("Admin username: ").strip()
password = getpass.getpass("Admin password: ")
if len(password) < 12:
    raise SystemExit("Use a password of at least 12 characters.")

db = SessionLocal()
if db.query(User).filter(User.username == username).first():
    raise SystemExit("That user already exists.")
db.add(User(username=username, password_hash=hash_password(password), role=UserRole.Admin))
db.commit()
print("Admin created.")
