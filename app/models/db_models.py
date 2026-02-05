"""
SQLAlchemy database models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
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

    recipes = relationship("Recipe", back_populates="project", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="project", cascade="all, delete-orphan")


class Recipe(Base):
    """Recipe model - represents a feature/recipe in a project"""
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.project_id"), nullable=False)
    recipe_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="recipes")
    chats = relationship("Chat", back_populates="recipe", cascade="all, delete-orphan")


class Chat(Base):
    """Chat model - represents a conversation session for follow-up questions"""
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey("projects.project_id"), nullable=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    analysis_type = Column(String(50), nullable=False)  # 'feasibility' or 'feature'
    analysis_context = Column(Text, nullable=True)  # Store the original analysis for context
    conversation_history = Column(Text, nullable=True)  # JSON string of conversation messages
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")
    recipe = relationship("Recipe", back_populates="chats")

