"""
Chat Node - Handles conversational responses with context and conversation history
"""

import json
import logging
from app.langgraph.unified_state import UnifiedAgentState
from app.services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


def create_chat_node() -> callable:
    """
    Create a chat node function for conversational responses.
    
    Returns:
        Node function for LangGraph
    """
    gemini_client = GeminiClient()

    def chat_node(state: UnifiedAgentState) -> UnifiedAgentState:
        """
        Chat agent that provides conversational responses with context.
        """
        try:
            logger.info(f"Running Chat agent for chat_id {state.get('chat_id')}")
            
            chat_id = state.get("chat_id")
            message = state.get("message", "")
            conversation_history = state.get("conversation_history", [])
            analysis_context = state.get("analysis_context", "")
            
            # Build conversation context
            system_prompt = """You are a helpful product strategy advisor helping a product manager understand their codebase and features. 
Write in business-friendly language. Focus on product impact, user experience, and business considerations. 
Avoid technical jargon, code references, or file names. Be conversational and helpful."""
            
            conversation_context = ""
            if analysis_context:
                conversation_context += f"Previous Analysis Context:\n{analysis_context}\n\n"
            
            if conversation_history:
                conversation_context += "Conversation History:\n"
                for msg in conversation_history:
                    role_label = "Product Manager" if msg.get("role") == "user" else "Assistant"
                    conversation_context += f"{role_label}: {msg.get('content', '')}\n\n"
            
            conversation_context += f"Product Manager: {message}\n\nAssistant:"
            
            # Generate response
            response_text = gemini_client.generate_content(
                conversation_context,
                system_prompt=system_prompt
            )
            
            # Add to conversation history
            updated_history = conversation_history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response_text}
            ]
            
            return {
                **state,
                "response": response_text,
                "conversation_history": updated_history,
                "messages": state.get("messages", []) + ["Chat response generated"]
            }
            
        except Exception as e:
            logger.error(f"Error in Chat agent: {str(e)}", exc_info=True)
            error_msg = f"Chat agent failed: {str(e)}"
            return {
                **state,
                "response": error_msg,
                "messages": state.get("messages", []) + [error_msg]
            }
    
    return chat_node

