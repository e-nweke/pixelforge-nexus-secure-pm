import os
import shutil
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    status,
    UploadFile,
)
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, Project, User, ProjectAssignment
from app.schemas import ProjectCreate, ProjectOut, UserRole
from app.services import project_service
from app.utils.session import get_session_user

router = APIRouter(prefix="/projects", tags=["Projects"])

templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/create", response_class=HTMLResponse)
def create_project_form(
    request: Request,
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user: User = db.query(User).get(user_id) if user_id else None
    if not user or user.role not in [UserRole.Admin]:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    project_leads = db.query(User).filter(User.role == UserRole.ProjectLead).all()
    return templates.TemplateResponse(
        "create_project.html",
        {"request": request, "user": user, "project_leads": project_leads},
    )


@router.post("/create", response_class=HTMLResponse)
def create_project_from_form(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    deadline: datetime = Form(...),
    lead_id: int = Form(...),
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user: User = db.query(User).get(user_id) if user_id else None
    if not user or user.role not in [UserRole.Admin]:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    lead = (
        db.query(User)
        .filter(User.id == lead_id, User.role == UserRole.ProjectLead)
        .first()
    )
    if not lead:
        return templates.TemplateResponse(
            "create_project.html",
            {
                "request": request,
                "user": user,
                "error": "Invalid Project Lead selected.",
                "project_leads": db.query(User)
                .filter(User.role == UserRole.ProjectLead)
                .all(),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    project_data = ProjectCreate(
        name=name, description=description, deadline=deadline, lead_id=lead_id
    )
    project_service.create_project(db, project_data)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@router.post(
    "/{project_id}/complete",
    response_model=ProjectOut,
)
def mark_project_completed(
    project_id: int,
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user: User = db.query(User).get(user_id) if user_id else None
    if not user or user.role not in [UserRole.Admin]:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    project = project_service.mark_as_completed(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/{project_id}", response_class=HTMLResponse)
def project_detail(
    project_id: int,
    request: Request,
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user: User = db.query(User).get(user_id) if user_id else None
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

    project: Project = db.query(Project).get(project_id)
    if not project:
        return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)

    # Only show to user if they are Admin, Project Lead for the project, or assigned Developer
    is_assigned = (
        user.role == UserRole.Admin
        or project.lead_id == user.id
        or db.query(ProjectAssignment)
        .filter_by(user_id=user.id, project_id=project_id)
        .first()
        is not None
    )
    if not is_assigned:
        return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)

    developers = db.query(User).filter(User.role == UserRole.Developer).all()
    documents = db.query(Document).filter_by(project_id=project_id).all()

    # Fetch assigned team members (all users assigned to this project)
    team_members = (
        db.query(User)
        .join(ProjectAssignment, ProjectAssignment.user_id == User.id)
        .filter(ProjectAssignment.project_id == project_id)
        .all()
    )

    return templates.TemplateResponse(
        "project_detail.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "developers": developers,
            "documents": documents,
            "team_members": team_members,
        },
    )


@router.post("/{project_id}/assign", response_class=HTMLResponse)
def assign_developer(
    project_id: int,
    developer_id: int = Form(...),
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user: User = db.query(User).get(user_id)
    project: Project = db.query(Project).get(project_id)

    if not user or not project:
        return RedirectResponse("/dashboard", status_code=302)

    if user.role != UserRole.Admin and project.lead_id != user.id:
        return RedirectResponse("/dashboard", status_code=302)

    developer: User = db.query(User).get(developer_id)
    if developer and developer.role == UserRole.Developer:
        # Check if already assigned
        assignment_exists = (
            db.query(ProjectAssignment)
            .filter_by(user_id=developer_id, project_id=project_id)
            .first()
        )
        if not assignment_exists:
            assignment = ProjectAssignment(user_id=developer_id, project_id=project_id)
            db.add(assignment)
            db.commit()

    return RedirectResponse(f"/projects/{project_id}", status_code=302)


@router.post("/{project_id}/upload", response_class=HTMLResponse)
def upload_document(
    project_id: int,
    document: UploadFile = File(...),
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user: User = db.query(User).get(user_id)
    project = db.query(Project).get(project_id)

    if not user or not project:
        return RedirectResponse("/dashboard", status_code=302)

    if user.role != UserRole.Admin and project.lead_id != user.id:
        return RedirectResponse("/dashboard", status_code=302)

    existing_docs = db.query(Document).filter_by(project_id=project_id).all()
    version = len(existing_docs) + 1

    stored_name = f"project_{project_id}_v{version}_{document.filename}"
    filepath = os.path.join(UPLOAD_DIR, stored_name)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(document.file, buffer)

    doc = Document(
        project_id=project_id,
        original_name=document.filename,
        stored_name=stored_name,
        version=version,
        uploaded_by_id=user.id,
        uploaded_at=datetime.now(),
    )
    db.add(doc)
    db.commit()

    return RedirectResponse(f"/projects/{project_id}", status_code=302)


@router.get("/docs/{doc_id}/download")
def download_document(
    doc_id: int,
    user_id: str = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    user: User = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    doc: Document = db.query(Document).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Only allow download if user is assigned to the project or is Admin or Project Lead
    # Get the project and its assigned developers
    project = doc.project
    assigned_user_ids = {assignment.user_id for assignment in project.team_assignments}

    if (
        user.role != UserRole.Admin
        and user.id != project.lead_id
        and user.id not in assigned_user_ids
    ):
        raise HTTPException(status_code=403, detail="Forbidden")

    file_path = os.path.join(UPLOAD_DIR, doc.stored_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=doc.original_name,
        media_type="application/octet-stream",
    )