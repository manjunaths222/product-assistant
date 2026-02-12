"""
Feature Discovery Service
Discovers all features in a codebase and analyzes each one
"""

import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.db_models import Project, ProjectFeature, Chat
from app.langgraph.tools.codex_terminal_runner import (
    run_codex_in_terminal,
    run_codex_raw_prompt,
)
from app.langgraph.nodes.feature_analysis_node import create_feature_analysis_node
from app.langgraph.state import FeatureAnalysisState
from app.services.gemini_client import GeminiClient
from datetime import datetime

logger = logging.getLogger(__name__)


class FeatureDiscoveryService:
    """Service for discovering and analyzing features in a codebase"""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.feature_analysis_node = create_feature_analysis_node()
    
    def discover_features_from_codebase(
        self,
        project_id: str,
        repo_path: str,
        db: Session,
        force: bool = False
    ) -> List[ProjectFeature]:
        """
        Discover all features in the codebase and analyze each one.
        
        Args:
            project_id: Project identifier
            repo_path: Path to the repository
            db: Database session
            force: If True, re-discover even if features already exist
            
        Returns:
            List of discovered ProjectFeature objects
        """
        try:
            # Check if features already exist
            existing_features = db.query(ProjectFeature).filter(
                ProjectFeature.project_id == project_id
            ).all()
            
            if existing_features and not force:
                logger.info(f"Features already exist for project {project_id}. Use force=True to re-discover.")
                return existing_features
            
            # If force=True, delete existing features
            if force and existing_features:
                logger.info(f"Deleting {len(existing_features)} existing features for project {project_id}")
                for feature in existing_features:
                    db.delete(feature)
                db.commit()
            
            # Step 1: Run Codex to discover all features in the codebase
            logger.info(f"Discovering features for project {project_id}...")
            feature_list = self._discover_feature_list(repo_path)
            
            if not feature_list:
                logger.warning(f"No features discovered for project {project_id}")
                return []
            
            # Step 2: For each feature, run detailed analysis using feature_analysis_node
            discovered_features = []
            for feature_name in feature_list:
                try:
                    logger.info(f"Analyzing feature: {feature_name}")
                    feature_analysis = self._analyze_feature(feature_name, repo_path)
                    
                    # Parse the analysis to extract required fields
                    parsed_feature = self._parse_feature_analysis(feature_name, feature_analysis)
                    
                    # Create chat session for this feature
                    chat = Chat(
                        project_id=project_id,
                        recipe_id=None,  # Kept for backward compatibility only
                        analysis_type="project_feature",
                        analysis_context=feature_analysis.get("feature_details", ""),
                        conversation_history="[]"
                    )
                    db.add(chat)
                    db.flush()
                    
                    # Create ProjectFeature
                    project_feature = ProjectFeature(
                        project_id=project_id,
                        chat_id=chat.id,
                        feature_name=parsed_feature["feature_name"],
                        high_level_overview=parsed_feature["high_level_overview"],
                        scope=parsed_feature["scope"],
                        dependencies=parsed_feature["dependencies"],
                        key_considerations=parsed_feature["key_considerations"],
                        limitations=parsed_feature["limitations"],
                        discovery_timestamp=datetime.utcnow()
                    )
                    db.add(project_feature)
                    discovered_features.append(project_feature)
                    
                except Exception as e:
                    logger.error(f"Error analyzing feature {feature_name}: {str(e)}", exc_info=True)
                    continue
            
            db.commit()
            
            # Refresh all features to get IDs
            for feature in discovered_features:
                db.refresh(feature)
            
            logger.info(f"Successfully discovered {len(discovered_features)} features for project {project_id}")
            return discovered_features
            
        except Exception as e:
            logger.error(f"Error in feature discovery: {str(e)}", exc_info=True)
            db.rollback()
            raise
    
    def _discover_feature_list(self, repo_path: str) -> List[str]:
        """
        Run Codex to discover all features in the codebase.
        
        Returns:
            List of feature names
        """
        prompt = """
You are a product domain analyst.

Your task is to analyze the codebase and output ONLY a numbered list of high-level product capabilities.

DO NOT ask questions.
DO NOT provide explanations.
DO NOT include conversational text.
Start immediately with the numbered list.

Definition:
A capability is a broad, stable product domain that groups related functionality.

A capability:
- Represents a major functional area of the system
- Groups multiple related features or services
- Would remain stable even if individual features change
- Reflects how the product is structured at a domain level

DO NOT list individual features, endpoints, APIs, or workflows.
DO NOT list low-level technical components.

Group granular functionality into broader domains.

Target:
Return between 5 and 10 capabilities.
Avoid being too granular.

Use clear noun phrases.

OUTPUT FORMAT (MANDATORY):
Start your response immediately with:
1. Capability Name 1
2. Capability Name 2
3. Capability Name 3

DO NOT include:
- Questions or requests for clarification
- Explanations or conversational text
- Status messages like "No capabilities found"
- Format descriptions or instructions
- Quoted text or choices

If no capabilities are found, output nothing (empty response).

Example CORRECT output:
1. User Authentication and Authorization
2. Document Management and Search
3. Legal Analysis and Intelligence
4. Reporting and Analytics
5. System Integration and Data Processing

Example INCORRECT output (DO NOT DO THIS):
I'm excited to help...
Which output do you want...
1. "Capability list only"
2. A 10‑section product analysis format
"""
        
        codex_output = run_codex_raw_prompt(repo_path, prompt)
        
        if not codex_output:
            logger.warning("Codex returned empty output for feature discovery")
            return []
        
        logger.info(f"Codex output for feature discovery: {codex_output}")
        
        # Check if output is conversational/question - if so, reject it
        conversational_starters = [
            "i'm", "i am", "i see", "i need", "i want", "i have",
            "you've", "you have", "you're", "you are",
            "which", "what", "how", "when", "where", "why",
            "please", "can you", "could you", "would you",
            "let me", "allow me", "excuse me",
        ]
        
        first_line_lower = codex_output.split('\n')[0].strip().lower()
        if any(first_line_lower.startswith(starter) for starter in conversational_starters):
            logger.warning("Codex returned conversational response instead of feature list. Rejecting output.")
            return []
        
        # Find the start of the numbered list - skip any conversational text before it
        lines = codex_output.split('\n')
        numbered_list_start = None
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # Look for the first numbered list item (must be at start of line)
            if re.match(r'^\d+\.\s+.+', line_stripped):
                numbered_list_start = i
                break
        
        # If no numbered list found, return empty (don't try to parse conversational text)
        if numbered_list_start is None:
            logger.warning("No numbered list found in Codex output. Output may be conversational.")
            return []
        
        # Parse only from the numbered list onwards
        feature_names = []
        for line in lines[numbered_list_start:]:
            line = line.strip()
            # Match numbered list items (1. Feature Name, 2. Feature Name, etc.)
            match = re.match(r'^\d+\.\s*(.+)$', line)
            if match:
                feature_name = match.group(1).strip()
                if feature_name and self._is_valid_feature_name(feature_name):
                    feature_names.append(feature_name)
            # Stop parsing if we hit a non-numbered line after finding features
            elif line and feature_names:
                # If we've found features and hit a non-numbered line, we're done
                break
        
        logger.info(f"Discovered {len(feature_names)} features: {feature_names}")
        return feature_names[:50]  # Limit to 50 features to avoid overwhelming the system
    
    def _is_valid_feature_name(self, name: str) -> bool:
        """
        Validate that a feature name is actually a feature, not instruction text.
        
        Args:
            name: Feature name to validate
            
        Returns:
            True if it appears to be a valid feature name
        """
        if not name or len(name) < 3:
            return False
        
        name_lower = name.lower().strip()
        
        # Filter out conversational/prompt-like text
        conversational_patterns = [
            'please tell me',
            'please',
            'tell me',
            'what is',
            'what are',
            'can you',
            'could you',
            'would you',
            'how do',
            'how does',
            'i need',
            'i want',
            'show me',
            'give me',
            'help me',
        ]
        
        # Check if name starts with conversational patterns
        for pattern in conversational_patterns:
            if name_lower.startswith(pattern):
                return False
        
        # Filter out status messages and instruction-like text
        status_message_patterns = [
            'no user-facing features',
            'no features detected',
            'no features found',
            'no feature',
            'features not found',
            'no capabilities',
            'unable to find',
            'cannot find',
        ]
        
        # Check if name is a status message
        for pattern in status_message_patterns:
            if pattern in name_lower:
                return False
        
        # Filter out quoted text (likely choices or options, not features)
        if (name.strip().startswith('"') and name.strip().endswith('"')) or \
           (name.strip().startswith("'") and name.strip().endswith("'")):
            return False
        
        # Filter out instruction-like text
        instruction_patterns = [
            'numbered list',
            'output format',
            'provide a',
            'only output',
            'nothing else',
            'example output',
            'feature name',
            'product analysis sections',
            'product analysis format',
            'section product analysis',
            'section format',
            'full product',
            'sections (',
            'format:',
            'output:',
            'rules:',
            'task:',
            'important:',
            'do not',
            'avoid listing',
            'focus on',
            'group related',
            'use clear',
            'list features',
        ]
        
        # Check if name contains instruction patterns
        for pattern in instruction_patterns:
            if pattern in name_lower:
                return False
        
        # Filter out format descriptions (contains both "section"/"analysis" and "format")
        if ('section' in name_lower or 'analysis' in name_lower) and 'format' in name_lower:
            return False
        
        # Filter out questions (ending with ?)
        if name.strip().endswith('?'):
            return False
        
        # Filter out lines that are clearly instructions (contain colons with specific keywords)
        if ':' in name and any(keyword in name_lower for keyword in ['format', 'output', 'example', 'rule', 'task', 'please', 'tell']):
            return False
        
        # Filter out very short phrases that end with colon (likely prompts)
        if name.strip().endswith(':') and len(name.strip()) < 30:
            # Allow colons if it's a reasonable feature name (like "User Management: Admin Panel")
            # But reject if it's too short or looks like a prompt
            if len(name.strip()) < 15 or any(word in name_lower for word in ['please', 'tell', 'what', 'how', 'can', 'could']):
                return False
        
        # Filter out lines that look like template placeholders
        if name_lower.startswith(('1.', '2.', '3.', 'feature name', 'example')):
            return False
        
        # Must contain at least one letter (not just numbers/symbols)
        if not re.search(r'[a-zA-Z]', name):
            return False
        
        # Feature names should be noun phrases, not questions or commands
        # Reject if it starts with question words or imperative verbs
        question_starters = ['what', 'where', 'when', 'why', 'who', 'how', 'which', 'whose']
        if any(name_lower.startswith(q + ' ') for q in question_starters):
            return False
        
        return True
    
    def _analyze_feature(self, feature_name: str, repo_path: str) -> Dict[str, Any]:
        """
        Analyze a single feature using feature_analysis_node.
        
        Args:
            feature_name: Name of the feature to analyze
            repo_path: Path to the repository
            
        Returns:
            Dictionary with high_level_design and feature_details
        """
        # Run Codex analysis for this specific feature
        query = f"Analyze the '{feature_name}' feature in this codebase. Provide a comprehensive analysis of what this feature does, its scope, dependencies, considerations, and limitations."
        codex_analysis = run_codex_in_terminal(repo_path, query)
        
        # Create state for feature_analysis_node
        state: FeatureAnalysisState = {
            "project_id": "",  # Not needed for analysis
            "recipe_id": None,  # No recipe needed - now optional
            "query": query,
            "repo_path": repo_path,
            "codebase_structure": {},
            "codex_analysis": codex_analysis,
            "high_level_design": "",
            "feature_details": "",
            "messages": []
        }
        
        # Run feature analysis node
        result = self.feature_analysis_node(state)
        
        return {
            "high_level_design": result.get("high_level_design", ""),
            "feature_details": result.get("feature_details", "")
        }
    
    def _parse_feature_analysis(self, feature_name: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse feature analysis to extract required fields.
        
        Args:
            feature_name: Name of the feature
            analysis: Dictionary with high_level_design and feature_details
            
        Returns:
            Dictionary with parsed feature data
        """
        feature_details = analysis.get("feature_details", "")
        high_level_design = analysis.get("high_level_design", "")
        
        # Extract sections from feature_details
        def _extract_section(text: str, heading: str) -> str:
            if heading not in text:
                return ""
            parts = text.split(heading, 1)
            if len(parts) > 1:
                # Get content until next ## heading
                content = parts[1].split("##", 1)[0].strip()
                return content
            return ""
        
        # Extract overview (from high_level_design or Feature Overview section)
        overview = high_level_design
        if not overview:
            overview = _extract_section(feature_details, "## Feature Overview")
        
        # Extract scope (from Key Capabilities or Product Integration)
        scope_parts = []
        capabilities = _extract_section(feature_details, "## Key Capabilities")
        if capabilities:
            scope_parts.append(capabilities)
        integration = _extract_section(feature_details, "## Product Integration")
        if integration:
            scope_parts.append(integration)
        scope = "\n\n".join(scope_parts) if scope_parts else overview
        
        # Extract dependencies
        dependencies_text = _extract_section(feature_details, "## Dependencies")
        dependencies = []
        if dependencies_text:
            # Parse bullet points or list items
            for line in dependencies_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('*') or line.startswith('•')):
                    dep = line.lstrip('-*•').strip()
                    if dep:
                        dependencies.append(dep)
                elif line and not line.startswith('#'):
                    dependencies.append(line)
        
        # Extract considerations
        considerations_text = _extract_section(feature_details, "## Considerations")
        considerations = []
        if considerations_text:
            for line in considerations_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('*') or line.startswith('•')):
                    cons = line.lstrip('-*•').strip()
                    if cons:
                        considerations.append(cons)
                elif line and not line.startswith('#'):
                    considerations.append(line)
        
        # Extract limitations (look for limitations section or infer from considerations)
        limitations_text = _extract_section(feature_details, "## Limitations")
        limitations = []
        if limitations_text:
            for line in limitations_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('*') or line.startswith('•')):
                    lim = line.lstrip('-*•').strip()
                    if lim:
                        limitations.append(lim)
                elif line and not line.startswith('#'):
                    limitations.append(line)
        
        return {
            "feature_name": feature_name,
            "high_level_overview": overview[:2000] if overview else "",  # Limit length
            "scope": scope[:2000] if scope else "",  # Limit length
            "dependencies": dependencies[:20] if dependencies else [],  # Limit to 20
            "key_considerations": considerations[:20] if considerations else [],  # Limit to 20
            "limitations": limitations[:20] if limitations else []  # Limit to 20
        }
