"""
Project Summary Service
Generates project summary, purpose, and tech stack from codebase analysis
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.db_models import Project
from app.services.gemini_client import GeminiClient
from app.services.git_service import GitService
from app.langgraph.tools.codex_terminal_runner import run_codex_raw_prompt

logger = logging.getLogger(__name__)


class ProjectSummaryService:
    """Service for generating project summary, purpose, and tech stack"""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.git_service = GitService()
    
    def generate_project_summary(
        self,
        project_id: str,
        repo_path: str,
        project_name: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Generate project summary, purpose, and tech stack from codebase analysis.
        
        Args:
            project_id: Project identifier
            repo_path: Path to the repository
            project_name: Optional project name
            db: Database session (optional, for updating project)
            
        Returns:
            Dictionary with summary, purpose, and tech_stack
        """
        try:
            logger.info(f"Generating project summary for project {project_id}")
            
            # Get codebase structure
            codebase_structure = self.git_service.get_codebase_structure(repo_path)
            
            # Collect key files for analysis (package.json, requirements.txt, README, etc.)
            key_files_info = self._collect_key_files(repo_path, codebase_structure)
            
            # Run Codex analysis to get codebase overview
            codex_analysis = self._analyze_codebase_with_codex(repo_path)
            
            # Generate summary, purpose, and tech stack using Gemini
            summary_result = self._generate_summary_with_gemini(
                codex_analysis=codex_analysis,
                key_files_info=key_files_info,
                project_name=project_name,
                codebase_structure=codebase_structure
            )
            
            # Parse the result
            parsed_result = self._parse_summary_result(summary_result)

            logger.info(f"Project summary generated successfully, Summary result: {parsed_result}")
            
            # Update project in database if db session provided
            if db:
                project = db.query(Project).filter(Project.project_id == project_id).first()
                if project:
                    project.summary = parsed_result.get("summary")
                    project.purpose = parsed_result.get("purpose")
                    project.tech_stack = parsed_result.get("tech_stack")
                    db.commit()
                    db.refresh(project)
                    logger.info(f"Updated project {project_id} with summary data")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error generating project summary: {str(e)}", exc_info=True)
            # Return empty result on error
            return {
                "summary": None,
                "purpose": None,
                "tech_stack": []
            }
    
    def _collect_key_files(self, repo_path: str, codebase_structure: dict) -> str:
        """
        Collect information from key files like package.json, requirements.txt, README, etc.
        
        Args:
            repo_path: Path to the repository
            codebase_structure: Codebase structure dictionary
            
        Returns:
            String with key files information
        """
        from pathlib import Path
        
        key_files = []
        repo_path_obj = Path(repo_path)
        
        # Common key files to check
        key_file_patterns = [
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Pipfile",
            "go.mod",
            "Cargo.toml",
            "pom.xml",
            "build.gradle",
            "README.md",
            "README.rst",
            "README.txt",
            ".gitignore",
            "Dockerfile",
            "docker-compose.yml",
            "Makefile"
        ]
        
        files = codebase_structure.get("files", [])
        for file_path in files:
            file_name = Path(file_path).name
            if file_name in key_file_patterns:
                full_path = repo_path_obj / file_path
                try:
                    if full_path.exists() and full_path.is_file():
                        content = full_path.read_text(errors="ignore")
                        # Limit content size to avoid token limits
                        if len(content) > 2000:
                            content = content[:2000] + "\n[Truncated...]"
                        key_files.append(f"File: {file_path}\n{content}\n")
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {str(e)}")
        
        return "\n---\n".join(key_files[:10])  # Limit to 10 files
    
    def _analyze_codebase_with_codex(self, repo_path: str) -> str:
        """
        Analyze codebase using Codex to get an overview from a product manager perspective.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Codex analysis text
        """
        prompt = """
You are a product strategist helping a product manager understand a software project. Analyze the codebase and provide a high-level overview from a product/business perspective.

Rules:
- Write for a product manager, NOT for engineers
- Focus on what the project does from a user/product perspective, not how it's built
- Use plain language - avoid technical jargon
- Focus on business value, user experience, and product capabilities

Provide:
1. What this project does (main purpose and functionality from a user/business perspective)
2. Key product capabilities and features (what users can do with this)
3. Business value and use cases (what problems it solves, who it serves)
4. Main product areas or domains (high-level functional areas, not technical components)

Keep it concise and focused on understanding the project's product purpose and business value.
"""
        
        codex_output = run_codex_raw_prompt(repo_path, prompt)
        return codex_output or ""
    
    def _generate_summary_with_gemini(
        self,
        codex_analysis: str,
        key_files_info: str,
        project_name: Optional[str],
        codebase_structure: dict
    ) -> str:
        """
        Generate project summary, purpose, and tech stack using Gemini.
        
        Args:
            codex_analysis: Analysis from Codex
            key_files_info: Information from key files
            project_name: Optional project name
            codebase_structure: Codebase structure dictionary
            
        Returns:
            Generated summary text
        """
        # Prepare codebase overview
        files_count = len(codebase_structure.get("files", []))
        dirs_count = len(codebase_structure.get("directories", []))
        
        codebase_overview = f"""
Codebase Overview:
- Total files: {files_count}
- Total directories: {dirs_count}
- Key directories: {', '.join(codebase_structure.get("directories", [])[:20])}
"""
        
        # Truncate codex analysis if too long
        analysis_snippet = codex_analysis[:3000] if len(codex_analysis) > 3000 else codex_analysis
        if not analysis_snippet:
            analysis_snippet = "No codebase analysis available."
        
        # Truncate key files info if too long
        files_snippet = key_files_info[:5000] if len(key_files_info) > 5000 else key_files_info
        if not files_snippet:
            files_snippet = "No key files found."
        
        prompt = f"""
You are a product strategy advisor helping a product manager understand a software project.

Rules:
- Write for a product manager, NOT for engineers
- Do NOT mention specific files, code, or technical implementation details
- Focus on business impact, user experience, and product considerations
- Use plain language - avoid technical jargon
- Explain what the project does from a user/product perspective, not how it's built
- For tech stack, focus on technologies that matter from a product/business perspective (platforms, frameworks that affect capabilities)

Task:
Analyze the codebase and provide:

1. **Project Summary**: A concise 2-3 sentence overview of what this project does from a product/business perspective - what value it provides, what users can do with it, and its role in the product ecosystem.

2. **Project Purpose**: A clear statement of the project's purpose from a business perspective - why it exists, what problem it solves, who it serves, and what business outcomes it enables.

3. **Tech Stack**: A list of technologies, platforms, and tools that are relevant from a product/business perspective. Focus on technologies that affect product capabilities, user experience, or business operations. Format as a simple list of technology names.

Project Name: {project_name or "Not specified"}

Codebase Analysis:
{analysis_snippet}

Key Files Information:
{files_snippet}

Codebase Structure:
{codebase_overview}

Output format (use this structure exactly):

## Project Summary
[2-3 sentence overview of what the project does from a product/business perspective]

## Project Purpose
[Clear statement of why the project exists, what problem it solves, and who it serves - from a business/product perspective]

## Tech Stack
[List technologies that matter from a product/business perspective, one per line:
- Technology 1
- Technology 2
- Technology 3
...]
"""
        
        system_prompt = """You are a product strategy advisor helping product managers understand software projects. 
Write in business-friendly language. Focus on product impact, user experience, and business considerations. 
Avoid technical jargon, code references, or file names. Be thorough, realistic, and professional."""
        
        result = self.gemini_client.generate_content(prompt, system_prompt=system_prompt)
        return result
    
    def _parse_summary_result(self, summary_text: str) -> Dict[str, Any]:
        """
        Parse the summary result into structured components.
        
        Args:
            summary_text: Generated summary text
            
        Returns:
            Dictionary with summary, purpose, and tech_stack
        """
        def _extract_section(text: str, heading: str) -> str:
            """Extract a section from the text by heading."""
            if heading not in text:
                return ""
            parts = text.split(heading, 1)
            if len(parts) > 1:
                # Get content until next ## heading
                content = parts[1].split("##", 1)[0].strip()
                return content
            return ""
        
        summary = _extract_section(summary_text, "## Project Summary")
        purpose = _extract_section(summary_text, "## Project Purpose")
        tech_stack_section = _extract_section(summary_text, "## Tech Stack")
        
        # Parse tech stack into list
        tech_stack = []
        if tech_stack_section:
            for line in tech_stack_section.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('*') or line.startswith('•')):
                    tech = line.lstrip('-*•').strip()
                    if tech:
                        tech_stack.append(tech)
                elif line and not line.startswith('#') and line:
                    tech_stack.append(line)
        
        return {
            "summary": summary or None,
            "purpose": purpose or None,
            "tech_stack": tech_stack[:50] if tech_stack else []  # Limit to 50 items
        }

