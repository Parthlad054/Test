#!/usr/bin/env python3
"""
Script to add employee value to the database enum and update existing data.
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
            # Check what enum types exist
            cur.execute("SELECT typname FROM pg_type WHERE typname LIKE '%role%'")
            results = cur.fetchall()
            print('Enum types found:', results)

            # Try to add employee to the enum
            for enum_type in results:
                try:
                    cur.execute(f"ALTER TYPE {enum_type[0]} ADD VALUE 'employee'")
                    print(f'Added employee to {enum_type[0]}')
                except Exception as e:
                    print(f'Could not add to {enum_type[0]}: {e}')

            # Now update the data
            try:
                cur.execute("UPDATE users SET role = 'employee' WHERE role = 'member'")
                users_updated = cur.rowcount
                print(f"Updated {users_updated} users from 'member' to 'employee'")
            except Exception as e:
                print(f"Error updating users: {e}")

            try:
                cur.execute("UPDATE project_members SET role = 'employee' WHERE role = 'member'")
                members_updated = cur.rowcount
                print(f"Updated {members_updated} project members from 'member' to 'employee'")
            except Exception as e:
                print(f"Error updating project_members: {e}")

        conn.commit()
        print("Database update completed!")

if __name__ == "__main__":
    main()