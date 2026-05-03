# Team Task Manager - Setup Instructions

## Requirements
- Python 3.9+
- PostgreSQL server
- Node.js & npm (for optionally serving frontend, though you can use any static server, or directly open `index.html` via a local server extension)

## Backend Setup
1. Open terminal and navigate to backend directory:
   `cd backend`
2. Create and activate a virtual environment:
   `python -m venv venv`
   `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
3. Install dependencies:
   `pip install -r requirements.txt`
4. Setup PostgreSQL database:
   - Make sure Postgres is running
   - Create a database called `taskmanager`
5. Configure `.env`:
   - An example `.env` is already provided. Make sure `DATABASE_URL` matches your local Postgres credentials.
6. Run the server:
   `uvicorn app.main:app --reload`
7. API Docs will be available at `http://localhost:8000/docs`

## Frontend Setup
1. Open terminal, navigate to `frontend` directory.
2. Serve using any simple static server, for example:
   `npx serve .` or `python -m http.server 3000`
3. Access the frontend app at the provided URL (e.g., `http://localhost:3000`).

---

## API Endpoints List

### Authentication
- `POST /auth/register`: Create a new user account.
- `POST /auth/login`: Authenticate user and receive access and refresh tokens.
- `POST /auth/refresh-token`: Refresh the access token.

### Users
- `GET /users/me`: Return current authenticated user.

### Projects
- `POST /projects`: Create a new project (You become the admin of this project).
- `GET /projects`: List all projects you are a member of.
- `POST /projects/{id}/members`: (Admin) Add a user to the project.

### Tasks
- `POST /tasks`: (Admin) Create a new task within a project and assign it to someone.
- `GET /tasks`: Retrieve tasks, supports `?project_id` and `?user_id` query filters.
- `PATCH /tasks/{id}/status`: Update the status of a task.
- `PATCH /tasks/{id}/assign`: (Admin) Re-assign the task.

### Dashboard
- `GET /dashboard`: Get statistics (`total_tasks`, `completed_tasks`, `pending_tasks`, `overdue_tasks`).
