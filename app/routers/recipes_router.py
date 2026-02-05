"""
Recipes API router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models.database import get_db
from app.models.db_models import Project, Recipe
from app.models.schemas import RecipeCreate, RecipeResponse, FeatureQueryRequest, FeatureQueryResponse
from app.langgraph.unified_orchestrator import UnifiedOrchestrator

router = APIRouter(prefix="/recipes", tags=["Recipes"])


@router.post("", response_model=RecipeResponse, status_code=201)
async def create_recipe(
    recipe_data: RecipeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new recipe for a project.
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.project_id == recipe_data.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{recipe_data.project_id}' not found")
        
        # Create recipe
        db_recipe = Recipe(
            project_id=recipe_data.project_id,
            recipe_name=recipe_data.recipe_name,
            description=recipe_data.description
        )
        db.add(db_recipe)
        db.commit()
        db.refresh(db_recipe)
        
        return db_recipe
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating recipe: {str(e)}")


@router.get("", response_model=List[RecipeResponse])
async def list_recipes(
    project_id: str = None,
    db: Session = Depends(get_db)
):
    """
    List all recipes. Optionally filter by project_id.
    """
    try:
        query = db.query(Recipe)
        if project_id:
            query = query.filter(Recipe.project_id == project_id)
        recipes = query.all()
        return recipes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing recipes: {str(e)}")


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific recipe by ID.
    """
    try:
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found")
        return recipe
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recipe: {str(e)}")


@router.post("/{recipe_id}/query", response_model=FeatureQueryResponse)
async def query_feature(
    recipe_id: int,
    request: FeatureQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query for feature details after analyzing the codebase.
    """
    try:
        # Get recipe
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found")
        
        # Get project
        project = db.query(Project).filter(Project.project_id == recipe.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{recipe.project_id}' not found")
        
        # Run feature analysis using unified orchestrator
        orchestrator = UnifiedOrchestrator()
        result = orchestrator.run(
            project_id=recipe.project_id,
            recipe_id=recipe_id,
            query=request.query,
            db=db
        )
        
        return FeatureQueryResponse(
            recipe_id=recipe_id,
            query=request.query,
            high_level_design=result.get("high_level_design", ""),
            feature_details=result.get("feature_details", ""),
            analysis_timestamp=datetime.utcnow(),
            chat_id=result.get("chat_id")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying feature: {str(e)}")

