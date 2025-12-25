import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api import chat, settings as settings_api, auth, profile, vacancies, resumes, automation, search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Job Search Assistant",
    description="AI-powered job search assistant with HH.ru integration",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(vacancies.router, prefix="/api/hh", tags=["vacancies"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])
app.include_router(automation.router, prefix="/api/automation", tags=["automation"])
app.include_router(search.router, prefix="/api/search", tags=["search"])


@app.get("/")
async def root():
    return {"message": "Job Search Assistant API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
