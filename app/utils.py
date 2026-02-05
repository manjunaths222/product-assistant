"""
Shared utility functions
"""

import logging
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.db_models import Project
from app.services.git_service import GitService

logger = logging.getLogger(__name__)
git_service = GitService()


def ensure_repo_exists(project: Project, db: Session) -> str:
    """
    Ensure the repository exists at the stored repo_path.
    If it doesn't exist, re-clone it from github_repo.
    
    Args:
        project: Project database object
        db: Database session
        
    Returns:
        Updated repo_path (may be the same or newly cloned)
        
    Raises:
        HTTPException: If repository doesn't exist and re-cloning fails
    """
    repo_path = project.repo_path
    
    # Check if repo_path exists
    if not Path(repo_path).exists():
        logger.warning(f"Repository path does not exist: {repo_path}. Attempting to re-clone...")
        if project.github_repo:
            try:
                logger.info(f"Re-cloning repository {project.github_repo} for project {project.project_id}...")
                repo_path = git_service.clone_or_pull_repo(project.github_repo, project.project_id)
                logger.info(f"Successfully re-cloned repository to {repo_path}")
                
                # Update repo_path in database
                project.repo_path = repo_path
                db.commit()
                db.refresh(project)
            except Exception as e:
                logger.error(f"Failed to re-clone repository: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Repository path does not exist and failed to re-clone: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Repository path does not exist and no github_repo available to re-clone"
            )
    
    return repo_path

