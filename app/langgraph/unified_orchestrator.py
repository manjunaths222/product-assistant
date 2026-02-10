"""
Unified Orchestrator - Routes between chat and analysis agents
Similar to Google ADK's coordinator pattern
"""

import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.langgraph.unified_state import UnifiedAgentState
from app.langgraph.unified_graph import create_unified_graph
from app.services.git_service import GitService
from app.models.db_models import Chat
from app.config import MAX_CONVERSATION_HISTORY_MESSAGES

logger = logging.getLogger(__name__)


def _create_chat_session(
    db: Session,
    project_id: str,
    analysis_type: str,
    analysis_context: str
) -> Optional[int]:
    """
    Helper function to create a chat session for follow-up questions.
    
    Returns:
        chat_id if successful, None otherwise
    """
    try:
        chat = Chat(
            project_id=project_id,
            recipe_id=None,  # Kept for backward compatibility only
            analysis_type=analysis_type,
            analysis_context=analysis_context,
            conversation_history="[]"
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        logger.info(f"Created chat session {chat.id} for {analysis_type} analysis")
        return chat.id
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}", exc_info=True)
        db.rollback()
        return None


class UnifiedOrchestrator:
    """Unified orchestrator that routes between chat and analysis agents"""
    
    def __init__(self):
        self.graph = create_unified_graph()
        self.git_service = GitService()
    
    def run(
        self,
        project_id: str,
        db: Optional[Session] = None,
        # Chat parameters
        chat_id: Optional[int] = None,
        message: Optional[str] = None,
        # Feature analysis parameters
        query: Optional[str] = None,
        # Feasibility analysis parameters
        requirement: Optional[str] = None,
        context: Optional[str] = None,
        # Common parameters
        repo_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the unified workflow that routes to appropriate agent.
        
        Args:
            project_id: Project identifier
            db: Database session
            chat_id: Chat ID for follow-up conversations
            message: User message for chat
            query: Query for feature analysis
            requirement: Requirement for feasibility analysis
            context: Context for feasibility analysis
            repo_path: Repository path (will be fetched from DB if not provided)
            
        Returns:
            Dictionary with results based on request type
        """
        try:
            # Get repo_path from database if not provided
            if not repo_path and db:
                from app.models.db_models import Project
                project = db.query(Project).filter(Project.project_id == project_id).first()
                if project:
                    repo_path = project.repo_path
            
            # Get codebase structure if repo_path is available
            codebase_structure = {}
            codex_analysis = ""
            
            # Codex analysis will be run by prepare_analysis_node in the graph workflow
            # No need to run it here - prepare_analysis_node handles it for all analysis requests
            
            # Load conversation history if chat_id is provided
            conversation_history = []
            analysis_context = None
            if chat_id and db:
                chat = db.query(Chat).filter(Chat.id == chat_id).first()
                if chat:
                    analysis_context = chat.analysis_context
                    if chat.conversation_history:
                        try:
                            conversation_history = json.loads(chat.conversation_history)
                            # Truncate to keep only recent messages to prevent context window overflow
                            original_length = len(conversation_history)
                            if original_length > MAX_CONVERSATION_HISTORY_MESSAGES:
                                # Keep the most recent messages (last N messages)
                                conversation_history = conversation_history[-MAX_CONVERSATION_HISTORY_MESSAGES:]
                                logger.warning(
                                    f"Truncated conversation history from {original_length} "
                                    f"to {len(conversation_history)} messages for chat_id {chat_id}"
                                )
                        except json.JSONDecodeError:
                            conversation_history = []
            
            # Don't set query/requirement from message yet - let router decide first
            # Only set them if router determines it's an analysis request
            effective_query = query
            effective_requirement = requirement
            
            # Build initial state
            # Don't set query/requirement from message yet - let router decide first
            # Router will set them if it determines analysis is needed
            initial_state: UnifiedAgentState = {
                "request_type": "chat",  # Will be determined by router
                "chat_id": chat_id,
                "project_id": project_id,
                "repo_path": repo_path,
                "codebase_structure": codebase_structure,
                "message": message,
                "conversation_history": conversation_history,
                "analysis_context": analysis_context,
                "recipe_id": None,  # No longer used
                "query": query,  # Only set if explicitly provided (not from message)
                "requirement": requirement,  # Only set if explicitly provided (not from message)
                "context": context,
                "high_level_design": None,
                "feature_details": None,
                "risks": [],
                "open_questions": [],
                "technical_feasibility": None,
                "rough_estimate": {},
                "task_breakdown": {},
                "codex_analysis": "",  # Will be populated by prepare_analysis_node
                "response": None,
                "messages": []
            }
            
            # Run the unified workflow
            final_state = self.graph.invoke(initial_state)
            
            # Build response based on request type
            request_type = final_state.get("request_type", "chat")
            result = {
                "status": "success",
                "request_type": request_type
            }
            
            if request_type == "chat":
                result["response"] = final_state.get("response")
                result["chat_id"] = chat_id
                
                # Update chat history in database
                if chat_id and db:
                    chat = db.query(Chat).filter(Chat.id == chat_id).first()
                    if chat:
                        updated_history = final_state.get("conversation_history", [])
                        # Truncate history before saving to prevent unbounded growth
                        if len(updated_history) > MAX_CONVERSATION_HISTORY_MESSAGES:
                            updated_history = updated_history[-MAX_CONVERSATION_HISTORY_MESSAGES:]
                            logger.info(
                                f"Truncated conversation history to {len(updated_history)} messages "
                                f"before saving for chat_id {chat_id}"
                            )
                        chat.conversation_history = json.dumps(updated_history)
                        db.commit()
                        logger.info(f"Updated chat history for chat_id {chat_id}")
            
            elif request_type == "feature_analysis":
                result["high_level_design"] = final_state.get("high_level_design")
                result["feature_details"] = final_state.get("feature_details")
                
                # Use effective query (could be from message or explicit query)
                effective_query = query or message or ""
                
                # Create chat session for follow-up (or update existing if from chat)
                if db:
                    analysis_context = f"""
Query: {effective_query}

Feature Overview:
{final_state.get("high_level_design", "")}

Feature Details:
{final_state.get("feature_details", "")}
"""
                    # If triggered from existing chat, update that chat with new analysis context
                    # Otherwise create new chat
                    if chat_id:
                        # Update existing chat with new analysis
                        chat = db.query(Chat).filter(Chat.id == chat_id).first()
                        if chat:
                            chat.analysis_context = analysis_context
                            chat.analysis_type = "feature"
                            db.commit()
                            result["chat_id"] = chat_id
                            logger.info(f"Updated chat {chat_id} with new feature analysis")
                    else:
                        # Create new chat session
                        result["chat_id"] = _create_chat_session(
                            db=db,
                            project_id=project_id,
                            analysis_type="feature",
                            analysis_context=analysis_context
                        )
            
            elif request_type == "feasibility_analysis":
                result["high_level_design"] = final_state.get("high_level_design")
                result["risks"] = final_state.get("risks", [])
                result["open_questions"] = final_state.get("open_questions", [])
                result["technical_feasibility"] = final_state.get("technical_feasibility")
                result["rough_estimate"] = final_state.get("rough_estimate", {})
                result["task_breakdown"] = final_state.get("task_breakdown", {})
                
                # Use effective requirement (could be from message or explicit requirement)
                effective_requirement = requirement or message or ""
                
                # Create chat session for follow-up (or update existing if from chat)
                if db:
                    analysis_context = f"""
Requirement: {effective_requirement}
Context: {context or "None provided"}

High-Level Approach:
{final_state.get("high_level_design", "")}

Feasibility: {final_state.get("technical_feasibility", "Unknown")}

Risks:
{chr(10).join(f"- {risk}" for risk in final_state.get("risks", []))}

Open Questions:
{chr(10).join(f"- {q}" for q in final_state.get("open_questions", []))}

Estimate: {final_state.get("rough_estimate", {})}
"""
                    # If triggered from existing chat, update that chat with new analysis context
                    # Otherwise create new chat
                    if chat_id:
                        # Update existing chat with new analysis
                        chat = db.query(Chat).filter(Chat.id == chat_id).first()
                        if chat:
                            chat.analysis_context = analysis_context
                            chat.analysis_type = "feasibility"
                            db.commit()
                            result["chat_id"] = chat_id
                            logger.info(f"Updated chat {chat_id} with new feasibility analysis")
                    else:
                        # Create new chat session
                        result["chat_id"] = _create_chat_session(
                            db=db,
                            project_id=project_id,
                            analysis_type="feasibility",
                            analysis_context=analysis_context
                        )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in unified orchestrator: {str(e)}", exc_info=True)
            raise
