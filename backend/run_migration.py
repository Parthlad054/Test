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


def main() -> None:
    backend_dir = Path(__file__).resolve().parent
    load_env_file(backend_dir / ".env")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Add it to backend/.env or environment.")

    migrations_dir = backend_dir / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        raise RuntimeError(f"No migration files found in: {migrations_dir}")

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            for migration_file in migration_files:
                sql = migration_file.read_text(encoding="utf-8")
                cur.execute(sql)
                print(f"Applied: {migration_file.name}")
    print("All migrations applied successfully.")


if __name__ == "__main__":
    main()
