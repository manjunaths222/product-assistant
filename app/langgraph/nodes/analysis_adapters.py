"""
Adapter nodes to bridge unified state with specific analysis states
"""

import logging
from app.langgraph.unified_state import UnifiedAgentState
from app.langgraph.state import FeatureAnalysisState, FeasibilityAnalysisState
from app.langgraph.nodes.feature_analysis_node import create_feature_analysis_node
from app.langgraph.nodes.feasibility_analysis_node import create_feasibility_analysis_node

logger = logging.getLogger(__name__)


def create_feature_analysis_adapter() -> callable:
    """Adapter to convert unified state to feature analysis state"""
    feature_node = create_feature_analysis_node()
    
    def adapter_node(state: UnifiedAgentState) -> UnifiedAgentState:
        """Convert unified state to feature analysis state, run analysis, convert back"""
        try:
            # Convert to FeatureAnalysisState
            feature_state: FeatureAnalysisState = {
                "project_id": state["project_id"],
                "recipe_id": None,  # No longer used
                "query": state.get("query", ""),
                "repo_path": state.get("repo_path"),
                "codebase_structure": state.get("codebase_structure", {}),
                "codex_analysis": state.get("codex_analysis", ""),
                "high_level_design": "",
                "feature_details": "",
                "messages": []
            }
            
            # Run feature analysis
            result = feature_node(feature_state)
            
            # Convert back to unified state
            return {
                **state,
                "high_level_design": result.get("high_level_design", ""),
                "feature_details": result.get("feature_details", ""),
                "messages": state.get("messages", []) + result.get("messages", [])
            }
        except Exception as e:
            logger.error(f"Error in feature analysis adapter: {str(e)}", exc_info=True)
            return {
                **state,
                "messages": state.get("messages", []) + [f"Feature analysis error: {str(e)}"]
            }
    
    return adapter_node


def create_feasibility_analysis_adapter() -> callable:
    """Adapter to convert unified state to feasibility analysis state"""
    feasibility_node = create_feasibility_analysis_node()
    
    def adapter_node(state: UnifiedAgentState) -> UnifiedAgentState:
        """Convert unified state to feasibility analysis state, run analysis, convert back"""
        try:
            # Convert to FeasibilityAnalysisState
            feasibility_state: FeasibilityAnalysisState = {
                "project_id": state["project_id"],
                "requirement": state.get("requirement", ""),
                "context": state.get("context"),
                "repo_path": state.get("repo_path"),
                "codebase_structure": state.get("codebase_structure", {}),
                "codex_analysis": state.get("codex_analysis", ""),
                "high_level_design": "",
                "risks": [],
                "open_questions": [],
                "technical_feasibility": "",
                "rough_estimate": {},
                "task_breakdown": {},
                "messages": []
            }
            
            # Run feasibility analysis
            result = feasibility_node(feasibility_state)
            
            # Convert back to unified state
            return {
                **state,
                "high_level_design": result.get("high_level_design", ""),
                "risks": result.get("risks", []),
                "open_questions": result.get("open_questions", []),
                "technical_feasibility": result.get("technical_feasibility", ""),
                "rough_estimate": result.get("rough_estimate", {}),
                "task_breakdown": result.get("task_breakdown", {}),
                "messages": state.get("messages", []) + result.get("messages", [])
            }
        except Exception as e:
            logger.error(f"Error in feasibility analysis adapter: {str(e)}", exc_info=True)
            return {
                **state,
                "messages": state.get("messages", []) + [f"Feasibility analysis error: {str(e)}"]
            }
    
    return adapter_node

