"""
Unified state schema for routing between chat and analysis agents
"""

from typing import Dict, Any, List, TypedDict, Optional, Literal


class UnifiedAgentState(TypedDict):
    """Unified state schema for routing between chat and analysis"""
    # Request type and routing
    request_type: Literal["chat", "feasibility_analysis", "feature_analysis"]
    chat_id: Optional[int]
    
    # Common fields
    project_id: str
    repo_path: Optional[str]
    codebase_structure: Dict[str, Any]
    
    # Chat-specific fields
    message: Optional[str]
    conversation_history: List[Dict[str, str]]
    analysis_context: Optional[str]
    
    # Feature analysis fields
    recipe_id: Optional[int]  # Deprecated - kept for backward compatibility only, always None
    query: Optional[str]
    high_level_design: Optional[str]
    feature_details: Optional[str]
    
    # Feasibility analysis fields
    requirement: Optional[str]
    context: Optional[str]
    risks: List[str]
    open_questions: List[str]
    technical_feasibility: Optional[str]
    rough_estimate: Dict[str, Any]
    task_breakdown: Dict[str, Any]
    
    # Codex analysis (shared)
    codex_analysis: str
    
    # Response
    response: Optional[str]
    messages: List[str]

