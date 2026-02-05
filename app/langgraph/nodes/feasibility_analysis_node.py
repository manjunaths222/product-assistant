"""
Feasibility Analysis Node
Analyzes feasibility of a new requirement
"""

import logging
from app.langgraph.state import FeasibilityAnalysisState
from app.services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


def create_feasibility_analysis_node() -> callable:
    """
    Create a Feasibility Analysis node function.
    
    Returns:
        Node function for LangGraph
    """
    gemini_client = GeminiClient()

    def feasibility_analysis_node(state: FeasibilityAnalysisState) -> FeasibilityAnalysisState:
        """
        Feasibility Analysis Agent.
        Uses Codex CLI analysis output to assess feasibility of a new requirement.
        """
        try:
            logger.info(f"Running Feasibility Analysis agent for project {state.get('project_id')}")
            
            codex_analysis = state.get("codex_analysis", "")
            requirement = state.get("requirement", "")
            context = state.get("context", "")
            
            analysis_snippet = (codex_analysis or "").strip()
            if len(analysis_snippet) > 6000:
                analysis_snippet = analysis_snippet[:6000] + "\n\n[Truncated: analysis exceeded 6000 characters]"
            if not analysis_snippet:
                analysis_snippet = "N/A"

            prompt = f"""
You are a product strategy advisor helping a product manager understand the feasibility of a new requirement.

Task:
Given the codebase analysis and new requirement, produce a business-friendly feasibility assessment that includes:
1. High-level approach (in business terms, not technical implementation)
2. Feasibility assessment (High/Medium/Low)
3. Business risks and challenges
4. Open questions that need product decisions
5. Rough time and effort estimates

Rules:
- Write for a product manager, NOT for engineers
- Do NOT mention specific files, code, or technical implementation details
- Focus on business impact, user experience, and product considerations
- Use plain language - avoid technical jargon
- If details are missing, call them out as assumptions or unknowns
- Use clear headings and bullet points
- Explain what the feature will do from a user/product perspective, not how it will be built

New Requirement:
{requirement}

Additional Context:
{context or "None provided"}

Codex CLI Analysis:
{analysis_snippet}

Output format (use this structure exactly):

## High-Level Approach
[Describe the approach in business and product terms. What will this feature enable? How will users interact with it? What are the key capabilities?]

## Feasibility Assessment
[Assess feasibility: High/Medium/Low with explanation in business terms. What makes this feasible or challenging from a product perspective?]

## Risks & Challenges
[List business and product risks:
- Risk 1: Description (focus on product impact, not technical details)
- Risk 2: Description
...]

## Open Questions
[List questions that need product decisions:
- Question 1 (product/business focused)
- Question 2
...]

## Rough Estimate
[Provide rough estimates:
- Development Time: [hours/days]
- Testing Time: [hours/days]
- Total Effort: [hours/days]
- Complexity: [Low/Medium/High]
- Story Points: [if applicable]
- Dependencies: [list dependencies in business terms]]
"""

            formatted_analysis = gemini_client.generate_content(
                prompt,
                system_prompt="""You are a product strategy advisor helping product managers understand feature feasibility. 
Write in business-friendly language. Focus on product impact, user experience, and business considerations. 
Avoid technical jargon, code references, or file names. Be thorough, realistic, and professional."""
            )
            
            # Parse the analysis into structured components
            # In production, you might want more sophisticated parsing
            risks = []
            open_questions = []
            rough_estimate = {}
            technical_feasibility = "Unknown"
            high_level_design = formatted_analysis
            
            # Simple parsing - extract sections
            def _section(text: str, heading: str) -> str:
                if heading not in text:
                    return ""
                return text.split(heading, 1)[1].split("##", 1)[0].strip()
            
            risks_section = _section(formatted_analysis, "## Risks & Challenges")
            if not risks_section:
                risks_section = _section(formatted_analysis, "## Risks")
            if risks_section:
                risks = [r.strip() for r in risks_section.split("-") if r.strip() and not r.strip().startswith("#")]
            
            questions_section = _section(formatted_analysis, "## Open Questions")
            if questions_section:
                open_questions = [q.strip() for q in questions_section.split("-") if q.strip() and not q.strip().startswith("#")]
            
            feasibility_section = _section(formatted_analysis, "## Feasibility Assessment")
            if feasibility_section:
                lower_section = feasibility_section.lower()
                if "high" in lower_section:
                    technical_feasibility = "High"
                elif "medium" in lower_section:
                    technical_feasibility = "Medium"
                elif "low" in lower_section:
                    technical_feasibility = "Low"
            
            estimate_section = _section(formatted_analysis, "## Rough Estimate")
            if estimate_section:
                rough_estimate = {
                    "raw_text": estimate_section.strip(),
                    "parsed": True
                }
            
            high_level_section = _section(formatted_analysis, "## High-Level Approach")
            if high_level_section:
                high_level_design = high_level_section
            
            return {
                "high_level_design": high_level_design,
                "risks": risks,
                "open_questions": open_questions,
                "technical_feasibility": technical_feasibility,
                "rough_estimate": rough_estimate,
                "messages": state.get("messages", []) + [f"Feasibility analysis completed for project {state.get('project_id')}"]
            }
            
        except Exception as e:
            logger.error(f"Error in Feasibility Analysis agent: {str(e)}", exc_info=True)
            error_msg = f"Feasibility Analysis agent failed: {str(e)}"
            return {
                "high_level_design": error_msg,
                "risks": [error_msg],
                "open_questions": [error_msg],
                "technical_feasibility": "Unknown",
                "rough_estimate": {"error": error_msg},
                "messages": state.get("messages", []) + [error_msg]
            }
    
    return feasibility_analysis_node
