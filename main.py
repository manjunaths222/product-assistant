"""
FastAPI application entry point
Product Assistant API - Agentic AI integration with Codex Product Assistant
"""

import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

from app.config import APP_NAME, APP_VERSION, APP_DESCRIPTION, HOST, PORT
from app.routers.health_router import router as health_router
from app.routers.projects_router import router as projects_router
from app.routers.chat_router import router as chat_router
from app.models.database import Base, engine
# Import models so SQLAlchemy can discover them
from app.models import db_models  # noqa: F401

# Load environment variables from .env file
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION
)

# Include routers
app.include_router(health_router)
app.include_router(projects_router)
app.include_router(chat_router)


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    print(f"{APP_NAME} v{APP_VERSION} starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    print(f"{APP_NAME} shutting down...")


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

