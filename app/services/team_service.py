from sqlalchemy.orm import Session

from app import models


def assign_developer_to_project(db: Session, project_id: int, user_id: int):
    existing = (
        db.query(models.ProjectAssignment)
        .filter_by(project_id=project_id, user_id=user_id)
        .first()
    )
    if existing:
        return False

    assignment = models.ProjectAssignment(project_id=project_id, user_id=user_id)
    db.add(assignment)
    db.commit()
    return True


def get_projects_for_developer(db: Session, user_id: int):
    return (
        db.query(models.Project)
        .join(
            models.ProjectAssignment,
            models.Project.id == models.ProjectAssignment.project_id,
        )
        .filter(models.ProjectAssignment.user_id == user_id)
        .all()
    )