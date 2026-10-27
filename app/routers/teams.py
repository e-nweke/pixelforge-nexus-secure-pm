from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ProjectOut, TeamAssignRequest
from app.services import team_service
from app.utils.dependencies import admin_or_lead

router = APIRouter(prefix="/teams", tags=["Team Assignment"])


@router.post("/assign", dependencies=[Depends(admin_or_lead)])
def assign_developer(payload: TeamAssignRequest, db: Session = Depends(get_db)):
    success = team_service.assign_developer_to_project(
        db, payload.project_id, payload.user_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Developer already assigned or invalid input",
        )
    return {"message": "Developer assigned successfully"}


@router.get("/developer/{user_id}", response_model=list[ProjectOut])
def get_developer_projects(user_id: int, db: Session = Depends(get_db)):
    return team_service.get_projects_for_developer(db, user_id)