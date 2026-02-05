"""
Projects API router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models.database import get_db
from app.models.db_models import Project
from app.models.schemas import ProjectCreate, ProjectResponse
from app.services.git_service import GitService
from app.langgraph.unified_orchestrator import UnifiedOrchestrator
from app.models.schemas import FeasibilityQueryRequest, FeasibilityQueryResponse
from app.utils import ensure_repo_exists

router = APIRouter(prefix="/projects", tags=["Projects"])
git_service = GitService()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    """
    Register a GitHub repository and create a project.
    Project ID is auto-generated if not provided.
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
        
        return FeasibilityQueryResponse(
            project_id=project_id,
            requirement=request.requirement,
            high_level_design=result.get("high_level_design", ""),
            risks=result.get("risks", []),
            open_questions=result.get("open_questions", []),
            technical_feasibility=result.get("technical_feasibility", "Unknown"),
            rough_estimate=result.get("rough_estimate", {}),
            task_breakdown=result.get("task_breakdown", {}),
            analysis_timestamp=datetime.utcnow(),
            chat_id=result.get("chat_id")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing feasibility: {str(e)}")

