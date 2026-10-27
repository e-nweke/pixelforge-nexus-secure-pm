from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import DocumentOut
from app.services import document_service
from app.utils.dependencies import admin_or_lead, get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload", response_model=DocumentOut, dependencies=[Depends(admin_or_lead)]
)
def upload_document(
    project_id: int,
    uploaded_by_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return document_service.save_document(db, project_id, uploaded_by_id, file)


@router.get("/project/{project_id}", response_model=List[DocumentOut])
def get_project_documents(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return document_service.get_documents_for_project(db, project_id)