"""
Feature Analysis Node
Analyzes a recipe/feature in the codebase
"""

import logging
from app.langgraph.state import FeatureAnalysisState
from app.services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


def create_feature_analysis_node() -> callable:
    """
    Create a Feature Analysis node function.
    
    Returns:
        Node function for LangGraph
    """
    gemini_client = GeminiClient()

    def feature_analysis_node(state: FeatureAnalysisState) -> FeatureAnalysisState:
        """
        Feature Analysis Agent.
        Uses Codex CLI analysis output to prepare feature details and high-level design.
        """
        try:
            logger.info(f"Running Feature Analysis agent for recipe {state.get('recipe_id')}")
            
            codex_analysis = state.get("codex_analysis", "")
            query = state.get("query", "")
            
            analysis_snippet = (codex_analysis or "").strip()
            if len(analysis_snippet) > 6000:
                analysis_snippet = analysis_snippet[:6000] + "\n\n[Truncated: analysis exceeded 6000 characters]"
            if not analysis_snippet:
                analysis_snippet = "N/A"

            prompt = f"""
You are a product analyst helping a product manager understand a feature in their codebase.

Task:
Given the codebase analysis and user query, produce a business-friendly feature analysis that includes:
1. What the feature does (from a user/product perspective)
2. Key capabilities and functionality
3. How it fits into the product
4. Dependencies on other features

Rules:
- Write for a product manager, NOT for engineers
- Do NOT mention specific files, code, technical implementation details, or API endpoints
- Focus on what the feature does, not how it's built
- Use plain language - avoid technical jargon
- If details are missing, call them out as assumptions or unknowns
- Use clear headings and bullet points
- Describe user-facing functionality and business logic

User Query:
{query}

Codex CLI Analysis:
{analysis_snippet}

Output format (use this structure exactly):

## Feature Overview
[Describe what this feature does from a user and product perspective. What problem does it solve? What capabilities does it provide?]

## Key Capabilities
[Break down the feature's main capabilities:
- What users can do with this feature
- Key functionality areas
- User interactions and workflows
- Business logic and rules]

## Product Integration
[Explain how this feature fits into the overall product:
- How it relates to other features
- User journey and experience
- Business value and impact]

## Dependencies
[List dependencies on other features or capabilities in business terms]

## Considerations
[Outline important considerations for product decisions, user experience, or business logic]
"""

            formatted_analysis = gemini_client.generate_content(
                prompt,
                system_prompt="""You are a product analyst helping product managers understand features in their codebase. 
Write in business-friendly language. Focus on what features do from a user and product perspective, not technical implementation. 
Avoid technical jargon, code references, file names, or API details. Be thorough and professional."""
            )
            
            # Split the analysis into feature overview and feature details
            # Simple parsing - in production, you might want more sophisticated parsing
            parts = formatted_analysis.split("## Key Capabilities")
            high_level_design = parts[0].replace("## Feature Overview", "").strip() if len(parts) > 0 else formatted_analysis
            feature_details = formatted_analysis.strip()  # Keep full analysis as feature details
            
            return {
                "high_level_design": high_level_design,
                "feature_details": feature_details,
                "messages": state.get("messages", []) + [f"Feature analysis completed for recipe {state.get('recipe_id')}"]
            }
            
        except Exception as e:
            logger.error(f"Error in Feature Analysis agent: {str(e)}", exc_info=True)
            error_msg = f"Feature Analysis agent failed: {str(e)}"
            return {
                "high_level_design": error_msg,
                "feature_details": error_msg,
                "messages": state.get("messages", []) + [error_msg]
            }
    
    return feature_analysis_node

