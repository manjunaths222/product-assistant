"""
Projects API router
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models.database import get_db
from app.models.db_models import Project, Feasibility, Chat, ProjectFeature
from app.models.schemas import ProjectCreate, ProjectResponse
from app.services.git_service import GitService
from app.langgraph.unified_orchestrator import UnifiedOrchestrator
from app.models.schemas import (
    FeasibilityQueryRequest, FeasibilityQueryResponse, ChatMessage,
    ProjectFeatureResponse, FeatureDiscoveryRequest, ChatMessageRequest, ChatMessageResponse
)
from app.services.feature_discovery_service import FeatureDiscoveryService
from app.utils import ensure_repo_exists

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])
git_service = GitService()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register a GitHub repository and create a project.
    Project ID is auto-generated if not provided.
    Feature discovery runs automatically in the background after project creation.
    """
    try:
        import uuid
        
        # Auto-generate project_id if not provided
        project_id = project_data.project_id
        if not project_id:
            # Generate a unique project_id based on UUID
            project_id = str(uuid.uuid4())
        else:
            # Check if custom project_id already exists
            existing_project = db.query(Project).filter(Project.project_id == project_id).first()
            if existing_project:
                raise HTTPException(status_code=400, detail=f"Project with ID '{project_id}' already exists")
        
        # Clone or pull the repository
        repo_path = git_service.clone_or_pull_repo(project_data.github_repo, project_id)
        
        # Create project in database with stored repo_path
        db_project = Project(
            project_id=project_id,
            github_repo=project_data.github_repo,
            repo_path=repo_path,  # Store the repository path
            description=project_data.description
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        # Trigger feature discovery in background using FastAPI BackgroundTasks
        background_tasks.add_task(
            discover_features_background_task,
            project_id=project_id,
            repo_path=repo_path,
            force=False
        )
        logger.info(f"Started background feature discovery for project {project_id}")
        
        return db_project
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db)
):
    """
    List all projects.
    """
    try:
        projects = db.query(Project).all()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing projects: {str(e)}")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific project by project_id.
    """
    try:
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting project: {str(e)}")


@router.post("/{project_id}/feasibility", response_model=FeasibilityQueryResponse)
async def analyze_feasibility(
    project_id: str,
    request: FeasibilityQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze feasibility of a new requirement for a project.
    """
    try:
        # Get project
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        # Ensure repository exists (re-clone if needed)
        ensure_repo_exists(project, db)

        # Run feasibility analysis using unified orchestrator
        orchestrator = UnifiedOrchestrator()
        result = orchestrator.run(
            project_id=project_id,
            requirement=request.requirement,
            context=request.context or "",
            db=db
        )
        
        # Persist feasibility to database
        chat_id = result.get("chat_id")
        analysis_timestamp = datetime.utcnow()
        
        db_feasibility = Feasibility(
            project_id=project_id,
            chat_id=chat_id,
            requirement=request.requirement,
            context=request.context or "",
            high_level_design=result.get("high_level_design", ""),
            risks=result.get("risks", []),
            open_questions=result.get("open_questions", []),
            technical_feasibility=result.get("technical_feasibility", "Unknown"),
            rough_estimate=result.get("rough_estimate", {}),
            task_breakdown=result.get("task_breakdown", {}),
            analysis_timestamp=analysis_timestamp
        )
        db.add(db_feasibility)
        db.commit()
        db.refresh(db_feasibility)
        
        return FeasibilityQueryResponse(
            feasibility_id=db_feasibility.id,
            project_id=project_id,
            requirement=request.requirement,
            high_level_design=result.get("high_level_design", ""),
            risks=result.get("risks", []),
            open_questions=result.get("open_questions", []),
            technical_feasibility=result.get("technical_feasibility", "Unknown"),
            rough_estimate=result.get("rough_estimate", {}),
            task_breakdown=result.get("task_breakdown", {}),
            analysis_timestamp=analysis_timestamp,
            chat_id=chat_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error analyzing feasibility: {str(e)}")


@router.get("/{project_id}/feasibilities", response_model=List[FeasibilityQueryResponse])
async def get_feasibilities(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all feasibility analyses for a project.
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        # Get all feasibilities for this project
        feasibilities = db.query(Feasibility).filter(Feasibility.project_id == project_id).order_by(Feasibility.analysis_timestamp.desc()).all()
        
        return [
            FeasibilityQueryResponse(
                feasibility_id=feasibility.id,
                project_id=feasibility.project_id,
                requirement=feasibility.requirement,
                high_level_design=feasibility.high_level_design or "",
                risks=feasibility.risks or [],
                open_questions=feasibility.open_questions or [],
                technical_feasibility=feasibility.technical_feasibility or "Unknown",
                rough_estimate=feasibility.rough_estimate or {},
                task_breakdown=feasibility.task_breakdown or {},
                analysis_timestamp=feasibility.analysis_timestamp,
                chat_id=feasibility.chat_id
            )
            for feasibility in feasibilities
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving feasibilities: {str(e)}")


@router.get("/{project_id}/feasibilities/{feasibility_id}", response_model=FeasibilityQueryResponse)
async def get_feasibility(
    project_id: str,
    feasibility_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific feasibility analysis by ID.
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        # Get feasibility
        feasibility = db.query(Feasibility).filter(
            Feasibility.id == feasibility_id,
            Feasibility.project_id == project_id
        ).first()
        
        if not feasibility:
            raise HTTPException(status_code=404, detail=f"Feasibility '{feasibility_id}' not found for project '{project_id}'")
        
        # Load chat history if chat_id exists
        chat_history = None
        if feasibility.chat_id:
            chat = db.query(Chat).filter(Chat.id == feasibility.chat_id).first()
            if chat and chat.conversation_history:
                try:
                    history_data = json.loads(chat.conversation_history)
                    chat_history = [
                        ChatMessage(
                            role=msg.get("role", "user"),
                            content=msg.get("content", ""),
                            timestamp=datetime.fromisoformat(msg["timestamp"]) if msg.get("timestamp") else None
                        )
                        for msg in history_data
                    ]
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Error parsing chat history for chat_id {feasibility.chat_id}: {str(e)}")
                    chat_history = []
        
        return FeasibilityQueryResponse(
            feasibility_id=feasibility.id,
            project_id=feasibility.project_id,
            requirement=feasibility.requirement,
            high_level_design=feasibility.high_level_design or "",
            risks=feasibility.risks or [],
            open_questions=feasibility.open_questions or [],
            technical_feasibility=feasibility.technical_feasibility or "Unknown",
            rough_estimate=feasibility.rough_estimate or {},
            task_breakdown=feasibility.task_breakdown or {},
            analysis_timestamp=feasibility.analysis_timestamp,
            chat_id=feasibility.chat_id,
            chat_history=chat_history
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving feasibility: {str(e)}")


def discover_features_background_task(
    project_id: str,
    repo_path: str,
    force: bool
):
    """
    Background task to discover features in the project codebase.
    Creates its own database session for thread safety.
    """
    try:
        # Create a new database session for the background task
        from app.models.database import SessionLocal
        bg_db = SessionLocal()
        try:
            discovery_service = FeatureDiscoveryService()
            discovery_service.discover_features_from_codebase(
                project_id=project_id,
                repo_path=repo_path,
                db=bg_db,
                force=force
            )
            logger.info(f"Background feature discovery completed for project {project_id}")
        except Exception as e:
            logger.error(f"Error in background feature discovery for project {project_id}: {str(e)}", exc_info=True)
        finally:
            bg_db.close()
    except Exception as e:
        logger.error(f"Error setting up background feature discovery: {str(e)}", exc_info=True)


@router.post("/{project_id}/features/discover")
async def discover_features(
    project_id: str,
    request: FeatureDiscoveryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Discover all features in the project codebase (runs in background).
    This can be triggered manually or runs automatically on project creation.
    Returns immediately with a status message. Features will be available via GET /projects/{project_id}/features once discovery completes.
    """
    try:
        # Get project
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        # Ensure repository exists
        ensure_repo_exists(project, db)
        
        # Add background task for feature discovery
        background_tasks.add_task(
            discover_features_background_task,
            project_id=project_id,
            repo_path=project.repo_path,
            force=request.force
        )
        
        logger.info(f"Started background feature discovery for project {project_id}")
        
        return {
            "status": "started",
            "message": f"Feature discovery started for project '{project_id}'. Check /projects/{project_id}/features for results once discovery completes.",
            "project_id": project_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error starting feature discovery: {str(e)}")


@router.get("/{project_id}/features", response_model=List[ProjectFeatureResponse])
async def get_features(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all discovered features for a project.
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        # Get all features for this project
        features = db.query(ProjectFeature).filter(
            ProjectFeature.project_id == project_id
        ).order_by(ProjectFeature.discovery_timestamp.desc()).all()
        
        return [
            ProjectFeatureResponse(
                feature_id=feature.id,
                project_id=feature.project_id,
                feature_name=feature.feature_name,
                high_level_overview=feature.high_level_overview,
                scope=feature.scope,
                dependencies=feature.dependencies or [],
                key_considerations=feature.key_considerations or [],
                limitations=feature.limitations or [],
                discovery_timestamp=feature.discovery_timestamp,
                chat_id=feature.chat_id
            )
            for feature in features
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving features: {str(e)}")


@router.get("/{project_id}/features/{feature_id}", response_model=ProjectFeatureResponse)
async def get_feature(
    project_id: str,
    feature_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific feature by ID.
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        # Get feature
        feature = db.query(ProjectFeature).filter(
            ProjectFeature.id == feature_id,
            ProjectFeature.project_id == project_id
        ).first()
        
        if not feature:
            raise HTTPException(
                status_code=404,
                detail=f"Feature '{feature_id}' not found for project '{project_id}'"
            )
        
        # Load chat history if chat_id exists
        chat_history = None
        if feature.chat_id:
            chat = db.query(Chat).filter(Chat.id == feature.chat_id).first()
            if chat and chat.conversation_history:
                try:
                    history_data = json.loads(chat.conversation_history)
                    chat_history = [
                        ChatMessage(
                            role=msg.get("role", "user"),
                            content=msg.get("content", ""),
                            timestamp=datetime.fromisoformat(msg["timestamp"]) if msg.get("timestamp") else None
                        )
                        for msg in history_data
                    ]
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Error parsing chat history for chat_id {feature.chat_id}: {str(e)}")
                    chat_history = []
        
        return ProjectFeatureResponse(
            feature_id=feature.id,
            project_id=feature.project_id,
            feature_name=feature.feature_name,
            high_level_overview=feature.high_level_overview,
            scope=feature.scope,
            dependencies=feature.dependencies or [],
            key_considerations=feature.key_considerations or [],
            limitations=feature.limitations or [],
            discovery_timestamp=feature.discovery_timestamp,
            chat_id=feature.chat_id,
            chat_history=chat_history
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving feature: {str(e)}")


