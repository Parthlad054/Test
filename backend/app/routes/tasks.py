from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.models import Task, User
from app.schemas.schemas import TaskCreate, TaskResponse, TaskStatusUpdate, TaskAssignUpdate, APIResponse
from app.dependencies import get_current_user
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=APIResponse[TaskResponse])
def create_task(task_in: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = task_service.create_task(task_in, db, current_user)
    return APIResponse(status_code=200, message="Task created", data=task)

@router.get("", response_model=APIResponse[List[TaskResponse]])
def get_tasks(
    project_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    tasks = task_service.get_tasks(db, current_user, project_id, user_id)
    return APIResponse(status_code=200, message="Tasks retrieved", data=tasks)

@router.patch("/{task_id}/status", response_model=APIResponse[TaskResponse])
def update_task_status(task_id: str, status_in: TaskStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = task_service.update_task_status(task_id, status_in, db, current_user)
    return APIResponse(status_code=200, message="Task status updated", data=task)

@router.patch("/{task_id}/assign", response_model=APIResponse[TaskResponse])
def assign_task(task_id: str, assign_in: TaskAssignUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = task_service.assign_task(task_id, assign_in, db, current_user)
    return APIResponse(status_code=200, message="Task assigned", data=task)
