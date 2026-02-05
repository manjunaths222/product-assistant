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


class ProjectResponse(BaseModel):
    """Schema for project response"""
    id: int
    project_id: str
    github_repo: str
    repo_path: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecipeCreate(BaseModel):
    """Schema for creating a recipe"""
    project_id: str = Field(..., description="Project identifier")
    recipe_name: str = Field(..., description="Recipe/feature name")
    description: Optional[str] = Field(None, description="Recipe description")


class RecipeResponse(BaseModel):
    """Schema for recipe response"""
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
    """Schema for feature query response"""
    recipe_id: int
    query: str
    high_level_design: str
    feature_details: str
    analysis_timestamp: datetime
    chat_id: Optional[int] = Field(None, description="Chat ID for follow-up conversations")


class FeasibilityQueryRequest(BaseModel):
    """Schema for feasibility query request"""
    requirement: str = Field(..., description="New requirement to analyze")
    context: Optional[str] = Field(None, description="Additional context")


class FeasibilityQueryResponse(BaseModel):
    """Schema for feasibility query response"""
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


class ChatMessage(BaseModel):
    """Schema for a chat message"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")


class ChatMessageRequest(BaseModel):
    """Schema for sending a chat message"""
    message: str = Field(..., description="User's message")


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    chat_id: int
    message: str
    response: str
    timestamp: datetime

