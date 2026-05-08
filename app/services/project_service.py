from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.models import Project, ProjectMember, RoleEnum, User, Task, TaskStatus, ProjectStatusEnum
from app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectMemberAdd


def _is_global_admin(user: User) -> bool:
    return getattr(user.role, "value", user.role) == RoleEnum.admin.value


def _get_project_or_404(db: Session, project_id: str) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_membership(db: Session, project_id: str, user_id: str) -> Optional[ProjectMember]:
    return db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()


def _require_member_or_admin(db: Session, project_id: str, current_user: User):
    if _is_global_admin(current_user):
        return
    member = _get_membership(db, project_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Only project members can access this resource")


def _require_project_admin_or_global(db: Session, project_id: str, current_user: User):
    if _is_global_admin(current_user):
        return
    member = _get_membership(db, project_id, current_user.id)
    if not member or member.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Project admin permissions required")


def _attach_project_meta(db: Session, project: Project, my_role: RoleEnum | None = None):
    owner = db.query(User).filter(User.id == project.owner_id).first()
    member_count = db.query(func.count(ProjectMember.user_id)).filter(
        ProjectMember.project_id == project.id
    ).scalar() or 0
    task_count = db.query(func.count(Task.id)).filter(Task.project_id == project.id).scalar() or 0

    setattr(project, "owner_name", owner.email if owner else "Unknown")
    setattr(project, "member_count", int(member_count))
    setattr(project, "task_count", int(task_count))
    if my_role:
        setattr(project, "my_role", my_role)
    return project


def create_project(project_in: ProjectCreate, db: Session, current_user: User) -> Project:
    if not _is_global_admin(current_user):
        raise HTTPException(status_code=403, detail="Only global admins can create projects")

    new_project = Project(
        name=project_in.name,
        description=project_in.description,
        owner_id=current_user.id
    )
    db.add(new_project)
    db.flush()

    db.add(ProjectMember(
        project_id=new_project.id,
        user_id=current_user.id,
        role=RoleEnum.admin
    ))
    db.commit()
    db.refresh(new_project)
    return _attach_project_meta(db, new_project, RoleEnum.admin)


def list_projects_for_user(db: Session, current_user: User, skip: int = 0, limit: int = 50) -> List[Project]:
    if _is_global_admin(current_user):
        projects = db.query(Project).offset(skip).limit(limit).all()
        return [_attach_project_meta(db, p, RoleEnum.admin) for p in projects]

    rows = (
        db.query(Project, ProjectMember.role)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .filter(ProjectMember.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    projects: List[Project] = []
    for project, role in rows:
        projects.append(_attach_project_meta(db, project, role))
    return projects


def get_project_details(db: Session, project_id: str, current_user: User):
    project = _get_project_or_404(db, project_id)
    _require_member_or_admin(db, project_id, current_user)

    owner = db.query(User).filter(User.id == project.owner_id).first()
    member_rows = (
        db.query(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .filter(ProjectMember.project_id == project_id)
        .all()
    )

    members = [
        {
            "user_id": user.id,
            "email": user.email,
            "role": member.role,
            "joined_at": member.joined_at
        }
        for member, user in member_rows
    ]

    total_tasks = db.query(func.count(Task.id)).filter(Task.project_id == project_id).scalar() or 0
    done_tasks = db.query(func.count(Task.id)).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.done
    ).scalar() or 0
    open_tasks = int(total_tasks) - int(done_tasks)

    by_status_rows = (
        db.query(Task.status, func.count(Task.id))
        .filter(Task.project_id == project_id)
        .group_by(Task.status)
        .all()
    )
    by_status = {status.value: int(count) for status, count in by_status_rows}

    setattr(project, "owner_name", owner.email if owner else "Unknown")
    setattr(project, "members", members)
    setattr(project, "task_summary", {
        "total_tasks": int(total_tasks),
        "open_tasks": int(open_tasks),
        "done_tasks": int(done_tasks),
        "by_status": by_status
    })
    return project


def update_project(project_id: str, payload: ProjectUpdate, db: Session, current_user: User) -> Project:
    project = _get_project_or_404(db, project_id)
    _require_project_admin_or_global(db, project_id, current_user)

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return _attach_project_meta(db, project)


def archive_project(project_id: str, db: Session, current_user: User) -> Project:
    if not _is_global_admin(current_user):
        raise HTTPException(status_code=403, detail="Only global admins can archive projects")

    project = _get_project_or_404(db, project_id)
    open_tasks = db.query(func.count(Task.id)).filter(
        Task.project_id == project_id,
        Task.status != TaskStatus.done
    ).scalar() or 0
    if open_tasks > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot archive project with open tasks"
        )

    project.status = ProjectStatusEnum.archived
    db.commit()
    db.refresh(project)
    return _attach_project_meta(db, project)


def restore_project(project_id: str, db: Session, current_user: User) -> Project:
    if not _is_global_admin(current_user):
        raise HTTPException(status_code=403, detail="Only global admins can restore projects")

    project = _get_project_or_404(db, project_id)
    if project.status == ProjectStatusEnum.active:
        raise HTTPException(status_code=400, detail="Project is already active")

    project.status = ProjectStatusEnum.active
    db.commit()
    db.refresh(project)
    return _attach_project_meta(db, project)


def add_project_member(project_id: str, member_in: ProjectMemberAdd, db: Session, current_user: User) -> ProjectMember:
    _get_project_or_404(db, project_id)
    _require_project_admin_or_global(db, project_id, current_user)

    target_user = db.query(User).filter(User.id == member_in.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User to add not found")

    existing_member = _get_membership(db, project_id, member_in.user_id)
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this project")

    new_member = ProjectMember(
        project_id=project_id,
        user_id=member_in.user_id,
        role=member_in.role
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


def remove_project_member(project_id: str, user_id: str, db: Session, current_user: User):
    project = _get_project_or_404(db, project_id)
    _require_project_admin_or_global(db, project_id, current_user)

    if user_id == project.owner_id:
        raise HTTPException(status_code=400, detail="Cannot remove the project owner")

    member = _get_membership(db, project_id, user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Project member not found")

    db.delete(member)
    db.commit()
