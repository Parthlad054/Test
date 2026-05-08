# Team Task Manager

Team Task Manager: a full-stack REST API built with FastAPI, PostgreSQL, and SQLAlchemy.

## Tech Stack
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic v2
- python-jose JWT
- bcrypt

## Setup Instructions
1. Clone the repo
   ```bash
   git clone <repo-url>
   cd unnati_deployment_repo
   ```
2. Copy `.env.example` to `.env` and fill in values
   ```bash
   copy .env.example .env
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Generate a secret key
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
5. Create database tables
   ```bash
   python create_db.py
   ```
6. Run the app
   ```bash
   uvicorn app.main:app --reload
   ```

## API Overview
| Tag | Method | Path | Auth Required | Admin Only |
| --- | --- | --- | --- | --- |
| Auth | POST | `/api/v1/auth/signup` | Yes | No |
| Auth | POST | `/api/v1/auth/login` | No | No |
| Auth | POST | `/api/v1/auth/refresh` | No | No |
| Auth | GET | `/api/v1/auth/me` | Yes | No |
| Projects | POST | `/api/v1/projects` | Yes | Yes |
| Projects | GET | `/api/v1/projects` | Yes | No |
| Projects | GET | `/api/v1/projects/{project_id}` | Yes | No |
| Projects | PUT | `/api/v1/projects/{project_id}` | Yes | No |
| Projects | PATCH | `/api/v1/projects/{project_id}/archive` | Yes | Yes |
| Projects | PATCH | `/api/v1/projects/{project_id}/restore` | Yes | Yes |
| Projects | POST | `/api/v1/projects/{project_id}/members` | Yes | Yes |
| Projects | DELETE | `/api/v1/projects/{project_id}/members/{user_id}` | Yes | Yes |
| Tasks | POST | `/api/v1/projects/{project_id}/tasks` | Yes | No |
| Tasks | GET | `/api/v1/projects/{project_id}/tasks` | Yes | No |
| Tasks | GET | `/api/v1/tasks/{task_id}` | Yes | No |
| Tasks | PUT | `/api/v1/tasks/{task_id}` | Yes | No |
| Tasks | DELETE | `/api/v1/tasks/{task_id}` | Yes | Yes |
| Tasks | PATCH | `/api/v1/tasks/{task_id}/status` | Yes | No |
| Tasks | GET | `/api/v1/tasks/{task_id}/history` | Yes | No |
| Dashboard | GET | `/api/v1/dashboard` | Yes | No |
| Users | GET | `/api/v1/users` | Yes | Yes |
| Users | GET | `/api/v1/users/{user_id}` | Yes | No |

## Roles
- **Admin**: Can create projects, archive/restore projects, add/remove project members, delete tasks, and access the full user list.
- **Employee**: Can view and update tasks assigned to them, create and join projects where they are a member, and access their own user info.

## Scripts
All utility scripts are located in the `scripts/` folder:
- `scripts/create_admin.py`
- `scripts/fix_enum.py`
- `scripts/update_roles.py`
- `scripts/run_migration.py`
- `scripts/run_my_migration.py`
