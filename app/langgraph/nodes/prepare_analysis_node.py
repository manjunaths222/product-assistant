"""
Prepare Analysis Node - Runs Codex analysis if needed for analysis requests
"""

import logging
from app.langgraph.unified_state import UnifiedAgentState
from app.langgraph.tools.codex_terminal_runner import run_codex_in_terminal
from app.services.git_service import GitService

logger = logging.getLogger(__name__)


def create_prepare_analysis_node() -> callable:
    """
    Create a prepare analysis node that runs Codex if needed.
    
    Returns:
        Node function for LangGraph
    """
    def prepare_analysis_node(state: UnifiedAgentState) -> UnifiedAgentState:
        """
        Prepare analysis by running Codex if needed.
        """
        try:
            request_type = state.get("request_type", "chat")
            repo_path = state.get("repo_path")
            codex_analysis = state.get("codex_analysis", "")
            
            # Only prepare for analysis requests
            if request_type in ["feature_analysis", "feasibility_analysis"]:
                # Run Codex if we have a query/requirement but no codex_analysis yet
                query = state.get("query", "")
                requirement = state.get("requirement", "")
                context = state.get("context", "")
                
                if repo_path and not state.get("codebase_structure"):
                    state = {
                        **state,
                        "codebase_structure": GitService().get_codebase_structure(repo_path)
                    }
                
                if (query or requirement) and not codex_analysis and repo_path:
                    full_query = query or f"{requirement}\n\nContext: {context or ''}"
                    logger.info(f"Running Codex analysis for {request_type}...")
                    codex_analysis = run_codex_in_terminal(repo_path, full_query)
                    if codex_analysis:
                        logger.info(f"Codex analysis completed for {request_type} -- {codex_analysis}")
                    else:
                        logger.warning("Codex analysis returned empty output.")
            
            return {
                **state,
                "codex_analysis": codex_analysis,
                "messages": state.get("messages", []) + ["Analysis preparation completed"]
            }
            
        except Exception as e:
            logger.error(f"Error in prepare analysis node: {str(e)}", exc_info=True)
            return {
                **state,
                "messages": state.get("messages", []) + [f"Prepare analysis error: {str(e)}"]
            }
    
    return prepare_analysis_node
