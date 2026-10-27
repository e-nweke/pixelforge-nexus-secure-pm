import os
import uuid
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app import models

UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_documents_for_project(db: Session, project_id: int):
    return (
        db.query(models.Document)
        .filter(models.Document.project_id == project_id)
        .order_by(models.Document.version.desc())
        .all()
    )


def save_document(db: Session, project_id: int, uploaded_by_id: int, file: UploadFile):
    original_name = file.filename
    ext = os.path.splitext(original_name)[1]

    # Determine latest version
    existing = (
        db.query(models.Document)
        .filter(
            models.Document.project_id == project_id,
            models.Document.original_name == original_name,
        )
        .order_by(models.Document.version.desc())
        .first()
    )

    new_version = (existing.version + 1) if existing else 1
    stored_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    doc = models.Document(
        original_name=original_name,
        stored_name=stored_name,
        version=new_version,
        uploaded_at=datetime.now(),
        project_id=project_id,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc