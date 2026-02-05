"""
Gemini API client for text generation using LangChain.
Copied from jira-planbot
"""

import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FALLBACK_MODEL

logger = logging.getLogger(__name__)


class GeminiClient:
    """Gemini API client using LangChain."""

    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.fallback_model = GEMINI_FALLBACK_MODEL
        
        if not self.api_key:
            raise ValueError("Gemini API not configured. Set GEMINI_API_KEY environment variable.")
        
        # Initialize primary model
        self.llm = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=self.api_key,
            temperature=0.7,
        )
        
        # Initialize fallback model if different
        self.fallback_llm = None
        if self.fallback_model and self.fallback_model != self.model:
            self.fallback_llm = ChatGoogleGenerativeAI(
                model=self.fallback_model,
                google_api_key=self.api_key,
                temperature=0.7,
            )

    def generate_content(self, prompt: str, system_prompt: Optional[str] = None, timeout_s: int = 60) -> str:
        """
        Generate content using Gemini API via LangChain.

        Args:
            prompt: User prompt.
            system_prompt: Optional system instruction.
            timeout_s: HTTP timeout in seconds (not used with LangChain, kept for compatibility).

        Returns:
            Generated text.
        """
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        try:
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            # Try fallback model if available
            if self.fallback_llm:
                logger.warning(
                    "Gemini model failed (%s). Retrying with fallback model (%s). Error: %s",
                    self.model,
                    self.fallback_model,
                    str(e),
                )
                try:
                    response = self.fallback_llm.invoke(messages)
                    return response.content.strip()
                except Exception as fallback_error:
                    logger.error(
                        f"Both Gemini models failed: primary ({self.model}) and fallback ({self.fallback_model}). "
                        f"Fallback error: {str(fallback_error)}",
                        exc_info=True,
                    )
                    raise
            logger.error(f"Error calling Gemini API: {str(e)}", exc_info=True)
            raise

