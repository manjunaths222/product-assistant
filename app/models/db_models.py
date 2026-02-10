"""
SQLAlchemy database models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.database import Base


class Project(Base):
    """Project model"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), unique=True, index=True, nullable=False)
    github_repo = Column(String(500), nullable=False)
    repo_path = Column(String(1000), nullable=False)  # Store the local repository path
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # recipes relationship removed - kept Recipe model for backward compatibility only
    chats = relationship("Chat", back_populates="project", cascade="all, delete-orphan")
    feasibilities = relationship("Feasibility", back_populates="project", cascade="all, delete-orphan")
    features = relationship("ProjectFeature", back_populates="project", cascade="all, delete-orphan")


class Recipe(Base):
    """Recipe model - DEPRECATED: Kept for backward compatibility only. Use ProjectFeature instead."""
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.project_id"), nullable=False)
    recipe_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships removed - kept model for backward compatibility only


class Chat(Base):
    """Chat model - represents a conversation session for follow-up questions"""
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.project_id"), nullable=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    analysis_type = Column(String(50), nullable=False)  # 'feasibility', 'feature', or 'project_feature'
    analysis_context = Column(Text, nullable=True)  # Store the original analysis for context
    conversation_history = Column(Text, nullable=True)  # JSON string of conversation messages
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")
    # recipe relationship removed - recipe_id column kept for backward compatibility only
    feasibilities = relationship("Feasibility", back_populates="chat", cascade="all, delete-orphan")
    features = relationship("ProjectFeature", back_populates="chat", cascade="all, delete-orphan")


class Feasibility(Base):
    """Feasibility model - stores feasibility analysis results"""
    __tablename__ = "feasibilities"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.project_id"), nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=True, index=True)
    requirement = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    high_level_design = Column(Text, nullable=True)
    risks = Column(JSON, nullable=True)  # List[str]
    open_questions = Column(JSON, nullable=True)  # List[str]
    technical_feasibility = Column(String(100), nullable=True)
    rough_estimate = Column(JSON, nullable=True)  # Dict[str, Any]
    task_breakdown = Column(JSON, nullable=True)  # Dict[str, Any]
    analysis_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")
    chat = relationship("Chat", back_populates="feasibilities")


class ProjectFeature(Base):
    """ProjectFeature model - stores discovered features from codebase analysis"""
    __tablename__ = "project_features"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.project_id"), nullable=False, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=True, index=True)
    feature_name = Column(String(500), nullable=False)
    high_level_overview = Column(Text, nullable=True)
    scope = Column(Text, nullable=True)
    dependencies = Column(JSON, nullable=True)  # List[str]
    key_considerations = Column(JSON, nullable=True)  # List[str]
    limitations = Column(JSON, nullable=True)  # List[str]
    discovery_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="features")
    chat = relationship("Chat", back_populates="features")

