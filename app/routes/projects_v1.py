from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import (
    APIResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithRoleResponse,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectMemberAdd,
    ProjectMemberResponse,
)
from app.services import project_service


router = APIRouter(prefix="/api/v1/projects", tags=["projects-v1"])


@router.post("", response_model=APIResponse[ProjectWithRoleResponse])
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = project_service.create_project(project_in, db, current_user)
    return APIResponse(status_code=200, message="Project created", data=project)


@router.get("", response_model=APIResponse[List[ProjectWithRoleResponse]])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    projects = project_service.list_projects_for_user(db, current_user, skip=skip, limit=limit)
    return APIResponse(status_code=200, message="Projects retrieved", data=projects)


@router.get("/{project_id}", response_model=APIResponse[ProjectDetailResponse])
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = project_service.get_project_details(db, project_id, current_user)
    return APIResponse(status_code=200, message="Project details retrieved", data=project)


@router.put("/{project_id}", response_model=APIResponse[ProjectResponse])
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = project_service.update_project(project_id, payload, db, current_user)
    return APIResponse(status_code=200, message="Project updated", data=project)


@router.patch("/{project_id}/archive", response_model=APIResponse[ProjectResponse])
def archive_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = project_service.archive_project(project_id, db, current_user)
    return APIResponse(status_code=200, message="Project archived", data=project)


@router.patch("/{project_id}/restore", response_model=APIResponse[ProjectResponse])
def restore_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = project_service.restore_project(project_id, db, current_user)
    return APIResponse(status_code=200, message="Project restored", data=project)


@router.post("/{project_id}/members", response_model=APIResponse[ProjectMemberResponse])
def add_member(
    project_id: str,
    member_in: ProjectMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = project_service.add_project_member(project_id, member_in, db, current_user)
    return APIResponse(status_code=200, message="Member added", data=member)


@router.delete("/{project_id}/members/{user_id}", response_model=APIResponse[dict])
def remove_member(
    project_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_service.remove_project_member(project_id, user_id, db, current_user)
    return APIResponse(status_code=200, message="Member removed", data={"project_id": project_id, "user_id": user_id})
