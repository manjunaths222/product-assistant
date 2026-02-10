"""
Service for Git operations
"""

import os
import logging
from pathlib import Path
from git import Repo
from app.config import GIT_REPO_BASE_PATH, GIT_BRANCH

logger = logging.getLogger(__name__)


class GitService:
    """Service for Git repository operations"""
    
    def __init__(self):
        self.repo_base_path = Path(GIT_REPO_BASE_PATH)
        self.branch = GIT_BRANCH
        # Create base directory if it doesn't exist
        self.repo_base_path.mkdir(parents=True, exist_ok=True)
    
    def clone_or_pull_repo(self, github_repo: str, project_id: str) -> str:
        """
        Clone or pull a Git repository for a specific project.
        
        Args:
            github_repo: GitHub repository URL
            project_id: Project identifier (used for directory name)
            
        Returns:
            Path to the repository
        """
        try:
            # Create project-specific directory
            repo_path = self.repo_base_path / project_id
            repo_path.mkdir(parents=True, exist_ok=True)
            
            # Check if repository already exists
            if (repo_path / ".git").exists():
                logger.info(f"Repository exists at {repo_path}, pulling latest changes...")
                repo = Repo(repo_path)
                origin = repo.remotes.origin
                origin.pull(self.branch)
                logger.info(f"Successfully pulled latest changes from {self.branch}")
            else:
                if not github_repo:
                    raise ValueError("GitHub repository URL is required.")
                
                logger.info(f"Cloning repository from {github_repo} to {repo_path}...")
                repo = Repo.clone_from(github_repo, repo_path, branch=self.branch)
                logger.info(f"Successfully cloned repository to {repo_path}")

            self._ensure_repo_is_usable(repo_path)
            return str(repo_path)
            
        except Exception as e:
            logger.error(f"Error cloning/pulling Git repository: {str(e)}", exc_info=True)
            raise

    def _ensure_repo_is_usable(self, repo_path: Path) -> None:
        """
        Validate that the repo path is a usable Git checkout with files.
        Raises an error if the repo is missing core git metadata or has no files.
        """
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(f"Repo at {repo_path} is missing .git directory.")

        if not (git_dir / "config").exists() or not (git_dir / "HEAD").exists():
            raise ValueError(f"Repo at {repo_path} has incomplete git metadata.")

        # Verify GitPython can load it
        Repo(repo_path)

        # Ensure there are actual files besides .git
        has_files = False
        for root, dirs, files in os.walk(repo_path):
            # Skip .git and common noise
            dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", "venv", "node_modules", ".venv"]]
            if files:
                has_files = True
                break

        if not has_files:
            raise ValueError(f"Repo at {repo_path} contains no files to analyze.")
    
    def get_codebase_structure(self, repo_path: str) -> dict:
        """
        Get the structure of the codebase.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dictionary containing codebase structure information
        """
        try:
            codebase_info = {
                "path": repo_path,
                "files": [],
                "directories": []
            }
            
            repo_path_obj = Path(repo_path)
            
            if not repo_path_obj.exists():
                logger.warning(f"Repository path does not exist: {repo_path}")
                return codebase_info
            
            # Walk through the repository and collect file information
            for root, dirs, files in os.walk(repo_path_obj):
                # Skip common directories
                dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", "venv", "node_modules", ".venv"]]
                
                for file in files:
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(repo_path_obj)
                    codebase_info["files"].append(str(relative_path))
                
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    relative_path = dir_path.relative_to(repo_path_obj)
                    codebase_info["directories"].append(str(relative_path))
            
            return codebase_info
            
        except Exception as e:
            logger.error(f"Error getting codebase structure: {str(e)}", exc_info=True)
            return {"path": repo_path, "files": [], "directories": []}
