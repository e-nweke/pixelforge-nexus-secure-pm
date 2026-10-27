from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class UserRole(str, Enum):
    Admin = "Admin"
    ProjectLead = "ProjectLead"
    Developer = "Developer"


class UserBase(BaseModel):
    username: str
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    name: str
    description: str
    deadline: datetime


class ProjectCreate(ProjectBase):
    lead_id: int
    pass


class ProjectOut(ProjectBase):
    id: int
    completed: bool
    lead_id: Optional[int]

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    original_name: str
    stored_name: str
    version: int
    uploaded_at: datetime
    project_id: int
    uploaded_by_id: int

    class Config:
        from_attributes = True


class AssignmentOut(BaseModel):
    id: int
    user_id: int
    project_id: int

    class Config:
        from_attributes = True


class TeamAssignRequest(BaseModel):
    project_id: int
    user_id: int


class Token(BaseModel):
    access_token: str
    token_type: str
    mfa_required: bool | None = False


class MFACode(BaseModel):
    code: str


class MFASetupResponse(BaseModel):
    secret: str
    uri: str