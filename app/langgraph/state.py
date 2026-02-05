"""
State schema for LangGraph workflows
"""

from typing import Dict, Any, List, TypedDict, Optional


class FeatureAnalysisState(TypedDict):
    """State schema for feature analysis workflow"""
    project_id: str
    recipe_id: int
    query: str
    repo_path: Optional[str]
    codebase_structure: Dict[str, Any]
    codex_analysis: str
    high_level_design: str
    feature_details: str
    messages: List[str]


class FeasibilityAnalysisState(TypedDict):
    """State schema for feasibility analysis workflow"""
    project_id: str
    requirement: str
    context: Optional[str]
    repo_path: Optional[str]
    codebase_structure: Dict[str, Any]
    codex_analysis: str
    high_level_design: str
    risks: List[str]
    open_questions: List[str]
    technical_feasibility: str
    rough_estimate: Dict[str, Any]
    task_breakdown: Dict[str, Any]
    messages: List[str]

