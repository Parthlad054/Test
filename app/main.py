from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.routes import auth_v1, projects_v1, tasks_v1, dashboard_v1
from app.routes.users_v1 import router as users_v1
from app.db.database import engine, Base, SessionLocal
from app.models.models import User, RoleEnum
from app.core.config import settings
from app.core.security import get_password_hash

# Create tables (for production use alembic, we use metadata.create_all for simplicity)

print("Creating tables...")
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Team Task Manager API")

def get_allowed_origins(origins: str) -> list[str]:
    if not origins:
        return ["*"]
    return [origin.strip() for origin in origins.split(",") if origin.strip()]

@app.on_event("startup")
def startup_event():
    try:
        db = SessionLocal()
        admin_email = settings.ADMIN_EMAIL
        admin_password = settings.ADMIN_PASSWORD
        admin_full_name = settings.ADMIN_FULL_NAME or "Admin User"

        if not admin_email or not admin_password:
            logging.warning("ADMIN_EMAIL or ADMIN_PASSWORD not configured; skipping admin user seeding")
            db.close()
            return

        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            admin_user = User(
                email=admin_email,
                full_name=admin_full_name,
                hashed_password=get_password_hash(admin_password),
                role=RoleEnum.admin,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logging.info(f"Admin user seeded: {admin_email}")
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
    allow_origins=get_allowed_origins(settings.ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_v1.router)
app.include_router(projects_v1.router)
app.include_router(tasks_v1.router)
app.include_router(dashboard_v1.router)
app.include_router(users_v1)

@app.get("/")
def read_root():
    return {"message": "Welcome to Team Task Manager API"}

