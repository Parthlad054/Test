from datetime import date, datetime, timedelta
from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session
from app.models.models import (
    Task,
    TaskStatus,
    TaskPriority,
    TaskStatusLog,
    Project,
    ProjectMember,
    User,
    ProjectStatusEnum,
    RoleEnum,
)
from app.schemas.schemas import DashboardResponse

def get_dashboard_stats(db: Session, current_user: User) -> DashboardResponse:
    base_query = db.query(Task).join(ProjectMember, Task.project_id == ProjectMember.project_id).filter(ProjectMember.user_id == current_user.id)
    
    total = base_query.count()
    completed = base_query.filter(Task.status == TaskStatus.done).count()
    pending = base_query.filter(Task.status == TaskStatus.todo).count()
    
    today = date.today()
    overdue = base_query.filter(Task.due_date < today, Task.status != TaskStatus.done).count()
    
    return DashboardResponse(
        total_tasks=total,
        completed_tasks=completed,
        pending_tasks=pending,
        overdue_tasks=overdue
    )


def _is_global_admin(current_user: User) -> bool:
    return getattr(current_user.role, "value", current_user.role) == RoleEnum.admin.value


def _task_to_dashboard_item(task: Task, project_name: str) -> dict:
    today = date.today()
    is_overdue = bool(task.due_date and task.due_date < today and task.status != TaskStatus.done)
    days_until_due = (task.due_date - today).days if task.due_date else None
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "project_id": task.project_id,
        "project_name": project_name,
        "created_by": task.created_by,
        "assigned_to": task.assigned_to,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "is_overdue": is_overdue,
        "days_until_due": days_until_due,
    }


def get_dashboard_v1(db: Session, current_user: User) -> dict:
    today = date.today()
    week_ago = datetime.utcnow() - timedelta(days=7)
    is_admin = _is_global_admin(current_user)

    if is_admin:
        visible_projects_query = db.query(Project)
    else:
        visible_projects_query = db.query(Project).join(
            ProjectMember, Project.id == ProjectMember.project_id
        ).filter(ProjectMember.user_id == current_user.id)

    total_projects = visible_projects_query.distinct(Project.id).count()

    my_open_tasks = db.query(Task).filter(
        Task.assigned_to == current_user.id,
        Task.status != TaskStatus.done
    ).count()

    overdue_query = db.query(Task, Project.name).join(Project, Task.project_id == Project.id)
    if not is_admin:
        overdue_query = overdue_query.join(
            ProjectMember, Task.project_id == ProjectMember.project_id
        ).filter(ProjectMember.user_id == current_user.id)
    overdue_query = overdue_query.filter(
        Task.assigned_to == current_user.id,
        Task.due_date < today,
        Task.status != TaskStatus.done
    )
    overdue_rows = overdue_query.order_by(Task.due_date.asc()).all()
    overdue_items = [_task_to_dashboard_item(task, project_name) for task, project_name in overdue_rows]

    completed_this_week = db.query(func.count(TaskStatusLog.id)).filter(
        TaskStatusLog.changed_by == current_user.id,
        TaskStatusLog.new_status == TaskStatus.done,
        TaskStatusLog.changed_at >= week_ago
    ).scalar() or 0

    my_tasks_rows = db.query(Task, Project.name).join(
        Project, Task.project_id == Project.id
    ).filter(
        Task.assigned_to == current_user.id
    ).order_by(Task.due_date.asc().nullslast(), Task.updated_at.desc()).all()
    my_tasks = [_task_to_dashboard_item(task, project_name) for task, project_name in my_tasks_rows]

    recent_project_rows = db.query(
        Task.project_id,
        func.max(Task.updated_at).label("last_activity"),
    ).filter(
        (Task.created_by == current_user.id) | (Task.assigned_to == current_user.id)
    ).group_by(Task.project_id).order_by(func.max(Task.updated_at).desc()).limit(5).all()

    project_ids = [row.project_id for row in recent_project_rows]
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    project_map = {project.id: project for project in projects}

    counts = db.query(
        Task.project_id,
        func.count(Task.id).label("task_count"),
        func.sum(case((Task.status != TaskStatus.done, 1), else_=0)).label("open_task_count"),
        func.sum(case((Task.assigned_to == current_user.id, 1), else_=0)).label("my_task_count"),
    ).filter(Task.project_id.in_(project_ids)).group_by(Task.project_id).all() if project_ids else []
    counts_map = {row.project_id: row for row in counts}

    recent_projects = []
    for row in recent_project_rows:
        project = project_map.get(row.project_id)
        if not project:
            continue
        count_row = counts_map.get(project.id)
        recent_projects.append({
            "id": project.id,
            "name": project.name,
            "task_count": int(count_row.task_count) if count_row else 0,
            "open_task_count": int(count_row.open_task_count) if count_row else 0,
            "my_task_count": int(count_row.my_task_count) if count_row else 0,
        })

    payload = {
        "summary": {
            "total_projects": int(total_projects),
            "my_open_tasks": int(my_open_tasks),
            "overdue_tasks": len(overdue_items),
            "tasks_completed_this_week": int(completed_this_week),
        },
        "my_tasks": my_tasks,
        "overdue_tasks": overdue_items,
        "recent_projects": recent_projects,
    }

    if is_admin:
        team_total_users = db.query(func.count(User.id)).scalar() or 0
        team_active_projects = db.query(func.count(Project.id)).filter(
            Project.status == ProjectStatusEnum.active
        ).scalar() or 0
        team_open_tasks = db.query(func.count(Task.id)).filter(Task.status != TaskStatus.done).scalar() or 0
        team_critical_tasks = db.query(func.count(Task.id)).filter(
            Task.status != TaskStatus.done,
            Task.priority == TaskPriority.critical
        ).scalar() or 0

        all_overdue_rows = db.query(Task, Project.name).join(Project, Task.project_id == Project.id).filter(
            Task.due_date < today,
            Task.status != TaskStatus.done
        ).order_by(Task.due_date.asc()).all()
        payload["team_summary"] = {
            "total_users": int(team_total_users),
            "active_projects": int(team_active_projects),
            "total_open_tasks": int(team_open_tasks),
            "critical_tasks": int(team_critical_tasks),
        }
        payload["all_overdue_tasks"] = [
            _task_to_dashboard_item(task, project_name) for task, project_name in all_overdue_rows
        ]

    return payload
