from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.models import User, TaskStatus, TaskPriority
from app.schemas.schemas import APIResponse, TaskCreate, TaskResponse, TaskDetailResponse, TaskUpdate, TaskStatusUpdate
from app.services import task_service


router = APIRouter(prefix="/api/v1", tags=["tasks-v1"])


@router.post("/projects/{project_id}/tasks", response_model=APIResponse[TaskResponse])
def create_project_task(
    project_id: str,
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = task_service.create_project_task(project_id, payload, db, current_user)
    return APIResponse(status_code=200, message="Task created", data=task)


@router.get("/projects/{project_id}/tasks", response_model=APIResponse[List[TaskResponse]])
def list_project_tasks(
    project_id: str,
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    assigned_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = task_service.list_project_tasks(project_id, db, current_user, status, priority, assigned_to)
    return APIResponse(status_code=200, message="Tasks retrieved", data=tasks)


@router.get("/tasks/{task_id}", response_model=APIResponse[TaskDetailResponse])
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = task_service.get_task_detail(task_id, db, current_user)
    return APIResponse(status_code=200, message="Task detail retrieved", data=task)


@router.put("/tasks/{task_id}", response_model=APIResponse[TaskResponse])
def update_task(
    task_id: str,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = task_service.update_task(task_id, payload, db, current_user)
    return APIResponse(status_code=200, message="Task updated", data=task)


@router.delete("/tasks/{task_id}", response_model=APIResponse[dict])
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_service.delete_task(task_id, db, current_user)
    return APIResponse(status_code=200, message="Task deleted", data={"task_id": task_id})


@router.patch("/tasks/{task_id}/status", response_model=APIResponse[TaskResponse])
def patch_task_status(
    task_id: str,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = task_service.patch_task_status(task_id, payload, db, current_user)
    return APIResponse(status_code=200, message="Task status updated", data=task)
