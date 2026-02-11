"""
Pydantic schemas for API requests/responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProjectCreate(BaseModel):
    """Schema for creating a project"""
    github_repo: str = Field(..., description="GitHub repository URL")
    description: Optional[str] = Field(None, description="Project description")
    project_id: Optional[str] = Field(None, description="Optional custom project identifier (auto-generated if not provided)")
    project_name: Optional[str] = Field(None, description="Optional project name")


class ProjectResponse(BaseModel):
    """Schema for project response"""
    id: int
    project_id: str
    project_name: Optional[str]
    github_repo: str
    repo_path: str
    description: Optional[str]
    summary: Optional[str]
    purpose: Optional[str]
    tech_stack: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecipeCreate(BaseModel):
    """DEPRECATED: Schema for creating a recipe - kept for backward compatibility only"""
    project_id: str = Field(..., description="Project identifier")
    recipe_name: str = Field(..., description="Recipe/feature name")
    description: Optional[str] = Field(None, description="Recipe description")


class RecipeResponse(BaseModel):
    """DEPRECATED: Schema for recipe response - kept for backward compatibility only"""
    id: int
    project_id: str
    recipe_name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeatureQueryRequest(BaseModel):
    """Schema for feature query request"""
    query: str = Field(..., description="Query about the feature")


class FeatureQueryResponse(BaseModel):
    """DEPRECATED: Schema for feature query response - kept for backward compatibility only"""
    recipe_id: Optional[int] = Field(None, description="Deprecated - always None")
    query: str
    high_level_design: str
    feature_details: str
    analysis_timestamp: datetime
    chat_id: Optional[int] = Field(None, description="Chat ID for follow-up conversations")


class FeasibilityQueryRequest(BaseModel):
    """Schema for feasibility query request"""
    requirement: str = Field(..., description="New requirement to analyze")
    context: Optional[str] = Field(None, description="Additional context")


class ChatMessage(BaseModel):
    """Schema for a chat message"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")


class FeasibilityQueryResponse(BaseModel):
    """Schema for feasibility query response"""
    feasibility_id: int
    project_id: str
    requirement: str
    high_level_design: str
    risks: List[str]
    open_questions: List[str]
    technical_feasibility: str
    rough_estimate: Dict[str, Any]
    task_breakdown: Dict[str, Any]
    analysis_timestamp: datetime
    chat_id: Optional[int] = Field(None, description="Chat ID for follow-up conversations")
    chat_history: Optional[List[ChatMessage]] = Field(None, description="Conversation history for this feasibility analysis")


class ChatMessageRequest(BaseModel):
    """Schema for sending a chat message"""
    message: str = Field(..., description="User's message")


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    chat_id: int
    message: str
    response: str
    timestamp: datetime


class ProjectFeatureResponse(BaseModel):
    """Schema for project feature response"""
    feature_id: int
    project_id: str
    feature_name: str
    high_level_overview: Optional[str]
    scope: Optional[str]
    dependencies: List[str]
    key_considerations: List[str]
    limitations: List[str]
    discovery_timestamp: datetime
    chat_id: Optional[int] = Field(None, description="Chat ID for follow-up conversations")
    chat_history: Optional[List[ChatMessage]] = Field(None, description="Conversation history for this feature")

    class Config:
        from_attributes = True


class FeatureDiscoveryRequest(BaseModel):
    """Schema for triggering feature discovery"""
    force: Optional[bool] = Field(False, description="Force re-discovery even if features already exist")


class ChatCreateRequest(BaseModel):
    """Schema for creating a chat"""
    project_id: str = Field(..., description="Project identifier")
    analysis_type: str = Field(..., description="Type of analysis: 'feasibility', 'project_feature', etc.")
    analysis_context: Optional[str] = Field(None, description="Context for the analysis")


class ChatResponse(BaseModel):
    """Schema for chat response"""
    chat_id: int
    project_id: str
    analysis_type: str
    created_at: datetime

    class Config:
        from_attributes = True

