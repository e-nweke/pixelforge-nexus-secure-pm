from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.schemas import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(Enum(UserRole), default=UserRole.Developer)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)

    projects_led = relationship("Project", back_populates="lead")
    assignments = relationship("ProjectAssignment", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    deadline = Column(DateTime)
    completed = Column(Boolean, default=False)
    lead_id = Column(Integer, ForeignKey("users.id"))

    lead = relationship("User", back_populates="projects_led")
    team_assignments = relationship("ProjectAssignment", back_populates="project")
    documents = relationship("Document", back_populates="project")


class ProjectAssignment(Base):
    __tablename__ = "project_assignments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))

    user = relationship("User", back_populates="assignments")
    project = relationship("Project", back_populates="team_assignments")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    original_name = Column(String)  # e.g., "design_spec.pdf"
    stored_name = Column(String)  # e.g., "design_spec_v3_uuid.pdf"
    version = Column(Integer, default=1)
    uploaded_at = Column(DateTime, default=datetime.now)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))

    project = relationship("Project", back_populates="documents")
    uploaded_by = relationship("User")