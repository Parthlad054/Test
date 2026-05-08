#!/usr/bin/env python3
"""
Script to create the admin user and update database roles.
Run this script to set up the initial admin user.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from app.db.database import engine
from app.services.auth_service import create_admin_user
from app.core.config import settings

def main():
    print("Setting up admin user...")

    # Create database session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Create the admin user
        admin_user = create_admin_user(
            email="parthlad125@gmail.com",
            password="Parth@123",
            full_name="Parth Lad",
            db=db
        )

        print(f"✅ Admin user created/updated successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role.value}")
        print(f"   Full Name: {admin_user.full_name}")

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()