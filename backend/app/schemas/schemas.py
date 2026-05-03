from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Generic, TypeVar, Dict
from datetime import datetime, date
from app.models.models import TaskStatus, TaskPriority, RoleEnum, ProjectStatusEnum

T = TypeVar('T')


def _password_validator(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(ch.isupper() for ch in value):
        raise ValueError("Password must include at least 1 uppercase letter")
    if not any(ch.isdigit() for ch in value):
        raise ValueError("Password must include at least 1 number")
    return value

class APIResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: Optional[T] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class ResetPasswordWithOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(ch.isupper() for ch in value):
            raise ValueError("Password must include at least 1 uppercase letter")
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Password must include at least 1 number")
        return value

# Tokens
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenRefresh(BaseModel):
    refresh_token: str

# Users
class UserCreate(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _password_validator(value)

class UserLogin(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: RoleEnum
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


class AuthTokens(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Projects
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    status: Optional[ProjectStatusEnum] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    status: ProjectStatusEnum
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class ProjectWithRoleResponse(ProjectResponse):
    my_role: RoleEnum
    owner_name: str
    member_count: int
    task_count: int

class ProjectMemberAdd(BaseModel):
    user_id: str
    role: RoleEnum = RoleEnum.member

class ProjectMemberResponse(BaseModel):
    project_id: str
    user_id: str
    role: RoleEnum
    joined_at: datetime
    class Config:
        from_attributes = True

class ProjectMemberUserResponse(BaseModel):
    user_id: str
    email: str
    role: RoleEnum
    joined_at: datetime

class TaskSummaryResponse(BaseModel):
    total_tasks: int
    open_tasks: int
    done_tasks: int
    by_status: Dict[str, int]

class ProjectDetailResponse(ProjectResponse):
    owner_name: str
    members: List[ProjectMemberUserResponse]
    task_summary: TaskSummaryResponse

# Tasks
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    project_id: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: TaskPriority = TaskPriority.medium
    due_date: Optional[date] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None

class TaskStatusUpdate(BaseModel):
    status: TaskStatus

class TaskAssignUpdate(BaseModel):
    assigned_to: Optional[str] = None
    assigned_to_id: Optional[str] = None

class TaskUserMiniResponse(BaseModel):
    id: str
    email: str

class TaskStatusLogResponse(BaseModel):
    old_status: TaskStatus
    new_status: TaskStatus
    changed_by: str
    changed_at: datetime

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    project_id: str
    created_by: str
    assigned_to: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[date]
    is_overdue: bool
    days_until_due: Optional[int]
    assigned_user_name: Optional[str] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class TaskDetailResponse(TaskResponse):
    assignee: Optional[TaskUserMiniResponse] = None
    creator: TaskUserMiniResponse

# Dashboard
class DashboardResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int


class DashboardSummary(BaseModel):
    total_projects: int
    my_open_tasks: int
    overdue_tasks: int
    tasks_completed_this_week: int


class DashboardTaskItem(BaseModel):
    id: str
    title: str
    description: Optional[str]
    project_id: str
    project_name: str
    created_by: int
    assigned_to: Optional[int]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    is_overdue: bool
    days_until_due: Optional[int]


class RecentProjectItem(BaseModel):
    id: str
    name: str
    task_count: int
    open_task_count: int
    my_task_count: int


class TeamSummary(BaseModel):
    total_users: int
    active_projects: int
    total_open_tasks: int
    critical_tasks: int


class DashboardV1Response(BaseModel):
    summary: DashboardSummary
    my_tasks: List[DashboardTaskItem]
    overdue_tasks: List[DashboardTaskItem]
    recent_projects: List[RecentProjectItem]
    team_summary: Optional[TeamSummary] = None
    all_overdue_tasks: Optional[List[DashboardTaskItem]] = None
