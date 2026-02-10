"""
Application configuration
Reads from .env file similar to jira-planbot
"""

import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Application settings
APP_NAME = "Product Assistant API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "API for product analysis and feasibility assessment using Agentic AI"

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://yml@localhost:5432/product_assistant"
)

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAOqBY9Oqrp7fRQB5yYymU0HYtuJOUMefA")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-pro")

# Codex Configuration
CODEX_AUTH_JSON = os.getenv("CODEX_AUTH_JSON", "")
CODEX_MODEL = os.getenv("CODEX_MODEL", "gpt-5-codex")
CODEX_FALLBACK_MODEL = os.getenv("CODEX_FALLBACK_MODEL", "gpt-5")

# Git Configuration
GIT_REPO_BASE_PATH = os.getenv("GIT_REPO_BASE_PATH", "/tmp/product-assistant-repos")
GIT_BRANCH = os.getenv("GIT_BRANCH", "main")

# Conversation History Configuration
# Maximum number of conversation messages to keep in history
# This prevents context window overflow and maintains performance
MAX_CONVERSATION_HISTORY_MESSAGES = int(os.getenv("MAX_CONVERSATION_HISTORY_MESSAGES", "20"))
