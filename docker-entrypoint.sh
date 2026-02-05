#!/bin/bash
set -e

# Configure Codex CLI auth via API key if provided.
# Prefer CODEX_API_KEY, fall back to OPENAI_API_KEY.
API_KEY="${CODEX_API_KEY:-${OPENAI_API_KEY}}"

if [ -n "$API_KEY" ]; then
    export OPENAI_API_KEY="$API_KEY"
    CODEX_CONFIG_DIR="${HOME}/.codex"
    CODEX_CONFIG_FILE="${CODEX_CONFIG_DIR}/config.toml"
    mkdir -p "$CODEX_CONFIG_DIR"
    cat > "$CODEX_CONFIG_FILE" <<'EOF'
preferred_auth_method = "apikey"
EOF
    echo "Codex CLI API key configured via OPENAI_API_KEY and preferred auth method set to apikey"
else
    echo "CODEX_API_KEY or OPENAI_API_KEY not set - skipping Codex API key configuration"
fi

# Run database initialization
python init_db.py || echo "Database initialization completed (or already exists)"

# Execute the main command
exec "$@"
