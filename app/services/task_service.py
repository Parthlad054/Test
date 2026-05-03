from datetime import date
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.models import Task, TaskStatusLog, ProjectMember, RoleEnum, User, TaskStatus, TaskPriority
from app.schemas.schemas import TaskCreate, TaskStatusUpdate, TaskUpdate, TaskAssignUpdate


def _is_global_admin(user: User) -> bool:
    return getattr(user.role, "value", user.role) == RoleEnum.admin.value


def _project_membership(db: Session, project_id: str, user_id: str) -> Optional[ProjectMember]:
    return db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()


def _require_project_member(db: Session, project_id: str, current_user: User) -> Optional[ProjectMember]:
    if _is_global_admin(current_user):
        return None
    membership = _project_membership(db, project_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Only project members can access project tasks")
    return membership


def _require_task_or_404(db: Session, task_id: str) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _validate_assignee_membership(db: Session, project_id: str, assigned_to: Optional[str]) -> None:
    if assigned_to is None:
        return
    is_member = _project_membership(db, project_id, assigned_to)
    if not is_member:
        raise HTTPException(status_code=400, detail="assigned_to must be a member of the project")


def _serialize_task(db: Session, task: Task):
    assignee = db.query(User).filter(User.id == task.assigned_to).first() if task.assigned_to else None
    creator = db.query(User).filter(User.id == task.created_by).first()
    today = date.today()
    is_overdue = bool(task.due_date and task.due_date < today and task.status != TaskStatus.done)
    days_until_due = (task.due_date - today).days if task.due_date else None
    setattr(task, "is_overdue", is_overdue)
    setattr(task, "days_until_due", days_until_due)
    setattr(task, "assigned_user_name", assignee.email if assignee else None)
    setattr(task, "created_by_name", creator.email if creator else None)
    return task


def _serialize_task_detail(db: Session, task: Task):
    task = _serialize_task(db, task)
    assignee = db.query(User).filter(User.id == task.assigned_to).first() if task.assigned_to else None
    creator = db.query(User).filter(User.id == task.created_by).first()
    setattr(task, "assignee", {"id": assignee.id, "email": assignee.email} if assignee else None)
    setattr(task, "creator", {"id": creator.id, "email": creator.email} if creator else None)
    return task


def create_project_task(project_id: str, payload: TaskCreate, db: Session, current_user: User):
    _require_project_member(db, project_id, current_user)
    if payload.due_date and payload.due_date < date.today():
        raise HTTPException(status_code=400, detail="due_date cannot be in the past on creation")
    _validate_assignee_membership(db, project_id, payload.assigned_to)

    task = Task(
        title=payload.title,
        description=payload.description,
        project_id=project_id,
        created_by=current_user.id,
        assigned_to=payload.assigned_to,
        status=TaskStatus.todo,
        priority=payload.priority,
        due_date=payload.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _serialize_task(db, task)


def list_project_tasks(
    project_id: str,
    db: Session,
    current_user: User,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assigned_to: Optional[str] = None,
):
    _require_project_member(db, project_id, current_user)
    query = db.query(Task).filter(Task.project_id == project_id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    tasks = query.order_by(Task.created_at.desc()).all()
    return [_serialize_task(db, task) for task in tasks]


def get_task_detail(task_id: str, db: Session, current_user: User):
    task = _require_task_or_404(db, task_id)
    _require_project_member(db, task.project_id, current_user)
    return _serialize_task_detail(db, task)


def update_task(task_id: str, payload: TaskUpdate, db: Session, current_user: User):
    task = _require_task_or_404(db, task_id)
    membership = _require_project_member(db, task.project_id, current_user)
    is_admin = _is_global_admin(current_user) or (membership and membership.role == RoleEnum.admin)
    updates = payload.model_dump(exclude_unset=True)

    if not is_admin:
        allowed_for_member = {"status"}
        invalid_fields = [key for key in updates.keys() if key not in allowed_for_member]
        if invalid_fields or (task.created_by != current_user.id and task.assigned_to != current_user.id):
            raise HTTPException(status_code=403, detail="Only status can be updated by task creator or assignee")

    if "due_date" in updates and updates["due_date"] and updates["due_date"] < date.today():
        raise HTTPException(status_code=400, detail="due_date cannot be in the past on creation")
    if "assigned_to" in updates:
        _validate_assignee_membership(db, task.project_id, updates["assigned_to"])

    old_status = task.status
    for key, value in updates.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)

    if "status" in updates and old_status != task.status:
        db.add(TaskStatusLog(
            task_id=task.id,
            old_status=old_status,
            new_status=task.status,
            changed_by=current_user.id
        ))
        db.commit()
    return _serialize_task(db, task)


def delete_task(task_id: str, db: Session, current_user: User):
    task = _require_task_or_404(db, task_id)
    membership = _project_membership(db, task.project_id, current_user.id)
    is_admin = _is_global_admin(current_user) or (membership and membership.role == RoleEnum.admin)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Project admin or global admin only")
    db.delete(task)
    db.commit()


def patch_task_status(task_id: str, payload: TaskStatusUpdate, db: Session, current_user: User):
    task = _require_task_or_404(db, task_id)
    membership = _require_project_member(db, task.project_id, current_user)
    is_admin = _is_global_admin(current_user) or (membership and membership.role == RoleEnum.admin)
    if not is_admin and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Only assignee or project admin can update status")

    old_status = task.status
    task.status = payload.status
    db.commit()
    db.refresh(task)

    db.add(TaskStatusLog(
        task_id=task.id,
        old_status=old_status,
        new_status=task.status,
        changed_by=current_user.id
    ))
    db.commit()
    return _serialize_task(db, task)


# Backward compatibility for existing dashboard routes.
def create_task(task_in: TaskCreate, db: Session, current_user: User):
    if not task_in.project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    return create_project_task(task_in.project_id, task_in, db, current_user)


def get_tasks(db: Session, current_user: User, project_id: Optional[str] = None, user_id: Optional[str] = None):
    if project_id:
        return list_project_tasks(project_id, db, current_user, assigned_to=user_id)
    memberships = db.query(ProjectMember).filter(ProjectMember.user_id == current_user.id).all()
    all_tasks = []
    for membership in memberships:
        all_tasks.extend(list_project_tasks(membership.project_id, db, current_user, assigned_to=user_id))
    return all_tasks


def update_task_status(task_id: str, status_in: TaskStatusUpdate, db: Session, current_user: User):
    return patch_task_status(task_id, status_in, db, current_user)


def assign_task(task_id: str, assign_in: TaskAssignUpdate, db: Session, current_user: User):
    assignee = assign_in.assigned_to if assign_in.assigned_to is not None else assign_in.assigned_to_id
    return update_task(task_id, TaskUpdate(assigned_to=assignee), db, current_user)
