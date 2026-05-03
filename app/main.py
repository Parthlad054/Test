from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.routes import auth, auth_v1, users, projects, projects_v1, tasks, tasks_v1, dashboard, dashboard_v1
from app.db.database import engine, Base, SessionLocal
from app.models.models import User, RoleEnum
from app.core.security import get_password_hash

# Create tables (for production use alembic, we use metadata.create_all for simplicity)

print("Creating tables...")
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Team Task Manager API")

@app.on_event("startup")
def startup_event():
    try:
        db = SessionLocal()
        existing_admin = db.query(User).filter(User.email == "parthlad4125@gmail.com").first()
        if not existing_admin:
            admin_user = User(
                email="parthlad4125@gmail.com",
                full_name="Parth Lad",
                hashed_password=get_password_hash("Admin@123"),
                role=RoleEnum.admin,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logging.info("Admin user seeded: parthlad4125@gmail.com")
        db.close()
    except Exception as e:
        logging.error(f"Error seeding admin user: {e}")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status_code": exc.status_code, "message": str(exc.detail), "data": None}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status_code": 422, "message": "Validation Error", "data": exc.errors()}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, change to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(auth_v1.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(projects_v1.router)
app.include_router(tasks.router)
app.include_router(tasks_v1.router)
app.include_router(dashboard.router)
app.include_router(dashboard_v1.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Team Task Manager API"}

