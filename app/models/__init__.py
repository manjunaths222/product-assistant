"""
Database models
"""

from app.models.database import Base, engine, get_db, SessionLocal
from app.models.db_models import Project
# Recipe model kept in db_models for backward compatibility only
from app.models.schemas import (
    ProjectCreate,
    ProjectResponse,
    FeatureQueryRequest,
    FeatureQueryResponse,
    FeasibilityQueryRequest,
    FeasibilityQueryResponse
)

__all__ = [
    "Base",
    "engine",
    "get_db",
    "SessionLocal",
    "Project",
    "ProjectCreate",
    "ProjectResponse",
    "FeatureQueryRequest",
    "FeatureQueryResponse",
    "FeasibilityQueryRequest",
    "FeasibilityQueryResponse",
]

