from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import auth, documents, projects, teams, users, pages

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PixelForge Nexus")

# Serve static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Route registrations
app.include_router(projects.router)
app.include_router(users.router)
app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(pages.router)