"""
Chat API router - Now uses unified orchestrator for all chat operations
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.models.database import get_db
from app.models.db_models import Chat
from app.models.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatMessage
)
from app.langgraph.unified_orchestrator import UnifiedOrchestrator

router = APIRouter(prefix="/chats", tags=["Chats"])
logger = logging.getLogger(__name__)


@router.post("/{chat_id}/message", response_model=ChatMessageResponse)
async def send_message(
    chat_id: int,
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message in a chat session and get a response using unified orchestrator.
    """
    try:
        # Get chat to retrieve project_id
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat '{chat_id}' not found")
        
        if not chat.project_id:
            raise HTTPException(status_code=400, detail="Chat must be associated with a project")
        
        # Use unified orchestrator for chat
        orchestrator = UnifiedOrchestrator()
        result = orchestrator.run(
            project_id=chat.project_id,
            chat_id=chat_id,
            message=request.message,
            db=db
        )
        
        return ChatMessageResponse(
            chat_id=chat_id,
            message=request.message,
            response=result.get("response", ""),
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


@router.get("/{chat_id}/history", response_model=List[ChatMessage])
async def get_chat_history(
    chat_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the conversation history for a chat.
    """
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat '{chat_id}' not found")
        
        conversation_history = []
        if chat.conversation_history:
            try:
                history_data = json.loads(chat.conversation_history)
                conversation_history = [
                    ChatMessage(
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                        timestamp=datetime.fromisoformat(msg["timestamp"]) if msg.get("timestamp") else None
                    )
                    for msg in history_data
                ]
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Error parsing chat history: {str(e)}")
                conversation_history = []
        
        return conversation_history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting chat history: {str(e)}")

