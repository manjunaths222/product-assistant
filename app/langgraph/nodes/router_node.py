"""
Router Node - Determines whether to route to chat or analysis agents
"""

import logging
from app.langgraph.unified_state import UnifiedAgentState
from app.services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


def create_router_node() -> callable:
    """
    Create a router node function that determines the request type.
    
    Returns:
        Node function for LangGraph
    """
    gemini_client = GeminiClient()

    def router_node(state: UnifiedAgentState) -> UnifiedAgentState:
        """
        Router agent that determines whether to route to chat or analysis.
        Can detect analysis requests even when in a chat session.
        """
        try:
            logger.info(f"Running Router agent for project {state.get('project_id')}")
            
            # Explicit parameters take priority (for direct API calls)
            # If query is provided, it's a feature analysis
            if state.get("query"):
                return {
                    **state,
                    "request_type": "feature_analysis",
                    "messages": state.get("messages", []) + ["Routing to feature analysis agent"]
                }
            
            # If requirement is provided, it's a feasibility analysis
            if state.get("requirement"):
                return {
                    **state,
                    "request_type": "feasibility_analysis",
                    "messages": state.get("messages", []) + ["Routing to feasibility analysis agent"]
                }
            
            # Get the user message (could be from chat or new request)
            message = state.get("message") or state.get("query") or state.get("requirement", "")
            
            if not message:
                # If chat_id exists but no message, default to chat
                if state.get("chat_id"):
                    return {
                        **state,
                        "request_type": "chat",
                        "messages": state.get("messages", []) + ["No message provided, routing to chat"]
                    }
                logger.warning("No message, query, or requirement found. Defaulting to chat.")
                return {
                    **state,
                    "request_type": "chat",
                    "messages": state.get("messages", []) + ["No clear intent, routing to chat"]
                }
            
            # If chat_id exists and we have analysis context, this is likely a follow-up question
            # Only route to analysis if explicitly asking for NEW analysis
            has_chat_context = state.get("chat_id") and state.get("analysis_context")
            
            if has_chat_context:
                # In a chat session - be more conservative, default to chat unless clearly asking for new analysis
                prompt = f"""
You are a routing agent. The user is in a chat session asking a follow-up question.

IMPORTANT: Default to "chat" unless they EXPLICITLY ask for a NEW analysis.

Route to analysis ONLY if they say things like:
- "Can you analyze..." or "Analyze the feasibility of..."
- "How does [specific feature] work?" (asking about a specific feature in codebase)
- "What is the feasibility of adding [new thing]?"

Route to "chat" for:
- Questions about estimates, risks, approach, questions (follow-ups)
- "Does this...", "Are these...", "What about...", "Can you explain..."
- Any clarification or follow-up question

User message: {message}

Respond with ONLY one word: "chat", "feasibility_analysis", or "feature_analysis"
"""
            else:
                # New request (no chat context) - can be more aggressive about routing to analysis
                prompt = f"""
You are a routing agent for a product assistant system. Analyze the user's request and determine the appropriate route.

Available routes:
1. "chat" - For general conversation or questions
2. "feasibility_analysis" - For analyzing the feasibility of a NEW requirement (keywords: "analyze feasibility", "can we add", "is it possible to", "estimate", "new requirement")
3. "feature_analysis" - For analyzing an EXISTING feature in the codebase (keywords: "how does", "explain the feature", "what does this feature do", "analyze the feature")

User request: {message}

Respond with ONLY one word: "chat", "feasibility_analysis", or "feature_analysis"
"""
            
            route_decision = gemini_client.generate_content(
                prompt,
                system_prompt="You are a routing agent. Analyze the user's intent carefully. If they want NEW analysis, route to analysis. If they're asking follow-ups, route to chat. Respond with only one word: chat, feasibility_analysis, or feature_analysis."
            )
            
            route_decision = route_decision.strip().lower()
            
            # Validate and set request type
            if "feasibility" in route_decision:
                request_type = "feasibility_analysis"
                # Extract requirement from message if not already set
                if not state.get("requirement") and message:
                    updated_state = {
                        **state,
                        "request_type": request_type,
                        "requirement": message,  # Set requirement for analysis
                        "messages": state.get("messages", []) + [f"Router determined: {request_type}"]
                    }
                else:
                    updated_state = {
                        **state,
                        "request_type": request_type,
                        "messages": state.get("messages", []) + [f"Router determined: {request_type}"]
                    }
            elif "feature" in route_decision and "analysis" in route_decision:
                request_type = "feature_analysis"
                # Extract query from message if not already set
                if not state.get("query") and message:
                    updated_state = {
                        **state,
                        "request_type": request_type,
                        "query": message,  # Set query for analysis
                        "messages": state.get("messages", []) + [f"Router determined: {request_type}"]
                    }
                else:
                    updated_state = {
                        **state,
                        "request_type": request_type,
                        "messages": state.get("messages", []) + [f"Router determined: {request_type}"]
                    }
            else:
                request_type = "chat"
                updated_state = {
                    **state,
                    "request_type": request_type,
                    "messages": state.get("messages", []) + [f"Router determined: {request_type}"]
                }
            
            logger.info(f"Router determined request type: {request_type} (message: {message[:50]}...)")
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in Router agent: {str(e)}", exc_info=True)
            # Default to chat on error
            return {
                **state,
                "request_type": "chat",
                "messages": state.get("messages", []) + [f"Router error, defaulting to chat: {str(e)}"]
            }
    
    return router_node

