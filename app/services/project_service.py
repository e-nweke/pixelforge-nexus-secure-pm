from sqlalchemy.orm import Session

from app import models, schemas


def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(
        name=project.name,
        description=project.description,
        deadline=project.deadline,
        lead_id=project.lead_id,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def mark_as_completed(db: Session, project_id: int):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        return None
    project.completed = True
    db.commit()
    db.refresh(project)
    return project