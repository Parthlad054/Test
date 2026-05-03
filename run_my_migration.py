import os
from sqlalchemy import create_engine, text
from app.core.config import settings

try:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        with open('migrations/004_otp_fields.sql', 'r') as f:
            sql = f.read()
            for statement in sql.split(';'):
                if statement.strip():
                    conn.execute(text(statement))
        conn.commit()
    print("Migration applied successfully!")
except Exception as e:
    print(f"Error applying migration: {e}")
