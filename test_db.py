import sys
import traceback
sys.path.append(r"F:\Code unnati test\backend")
from app.db.database import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

try:
    db = SessionLocal()
    print("Testing password hashing...")
    hashed_pass = get_password_hash("password123")
    print("Hashing successful.")
    new_user = User(email="parthlad4125@gmail.com", hashed_password=hashed_pass)
    db.add(new_user)
    db.commit()
    print("User created successfully.")
except Exception as e:
    print("Error occurred!")
    traceback.print_exc()
