#!/usr/bin/env python3
"""
Script to update existing member roles to employee roles.
"""

import os
from pathlib import Path
import psycopg2

def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())

def main():
    backend_dir = Path(__file__).resolve().parent
    load_env_file(backend_dir / ".env")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Add it to .env or environment.")

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            # Update users table
            cur.execute("UPDATE users SET role = 'employee' WHERE role = 'member'")
            users_updated = cur.rowcount
            print(f"Updated {users_updated} users from 'member' to 'employee'")

            # Update project_members table
            cur.execute("UPDATE project_members SET role = 'employee' WHERE role = 'member'")
            members_updated = cur.rowcount
            print(f"Updated {members_updated} project members from 'member' to 'employee'")

        conn.commit()
        print("Database update completed successfully!")

if __name__ == "__main__":
    main()