from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import Project, ProjectMember, User
from app.schemas.schemas import ProjectCreate, ProjectResponse, ProjectWithRoleResponse, ProjectMemberAdd, ProjectMemberResponse, APIResponse
from app.dependencies import get_current_user
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=APIResponse[ProjectResponse])
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = project_service.create_project(project_in, db, current_user)
    return APIResponse(status_code=200, message="Project created", data=project)

@router.get("", response_model=APIResponse[List[ProjectWithRoleResponse]])
def get_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = project_service.list_projects_for_user(db, current_user)
    return APIResponse(status_code=200, message="Projects retrieved", data=projects)

@router.post("/{project_id}/members", response_model=APIResponse[ProjectMemberResponse])
def add_project_member(project_id: str, member_in: ProjectMemberAdd, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = project_service.add_project_member(project_id, member_in, db, current_user)
    return APIResponse(status_code=200, message="Member added", data=member)
