from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.db.database import Base

class RoleEnum(str, enum.Enum):
    admin = "admin"
    employee = "employee"

class ProjectStatusEnum(str, enum.Enum):
    active = "active"
    archived = "archived"

class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    in_review = "in_review"
    done = "done"

class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.employee, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    otp_used = Column(Boolean, default=False, nullable=True)

class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ProjectStatusEnum), default=ProjectStatusEnum.active, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User")
    tasks = relationship("Task", back_populates="project")
    members = relationship("ProjectMember", back_populates="project")

class ProjectMember(Base):
    __tablename__ = "project_members"
    project_id = Column(String(36), ForeignKey("projects.id"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role = Column(Enum(RoleEnum), default=RoleEnum.employee)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="members")
    user = relationship("User")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.todo, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.medium, nullable=False)
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])

class TaskStatusLog(Base):
    __tablename__ = "task_status_logs"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    old_status = Column(Enum(TaskStatus), nullable=False)
    new_status = Column(Enum(TaskStatus), nullable=False)
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
