#!/bin/bash
set -e

# Authenticate Codex CLI if API key is provided
# Try CODEX_API_KEY first, then fall back to OPENAI_API_KEY
API_KEY="${CODEX_API_KEY:-${OPENAI_API_KEY}}"

if [ -n "$API_KEY" ]; then
    echo "Authenticating Codex CLI..."
    echo "$API_KEY" | codex login --with-api-key || echo "Codex authentication failed - continuing without it"
else
    echo "CODEX_API_KEY or OPENAI_API_KEY not set - skipping Codex authentication"
fi

# Run database initialization
python init_db.py || echo "Database initialization completed (or already exists)"

# Execute the main command
exec "$@"

