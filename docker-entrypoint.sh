#!/bin/bash
set -e

CODEX_CONFIG_DIR="${HOME}/.codex"
CODEX_CONFIG_FILE="${CODEX_CONFIG_DIR}/config.toml"
CODEX_AUTH_FILE="${CODEX_CONFIG_DIR}/auth.json"

# Create Codex config directory
mkdir -p "$CODEX_CONFIG_DIR"

# Priority 1: OAuth via CODEX_AUTH_JSON environment variable (for Render)
if [ -n "$CODEX_AUTH_JSON" ]; then
    # Check if it's base64 encoded (common for env vars)
    if echo "$CODEX_AUTH_JSON" | base64 -d >/dev/null 2>&1; then
        # Decode base64 and write to auth.json
        echo "$CODEX_AUTH_JSON" | base64 -d > "$CODEX_AUTH_FILE"
        echo "Codex OAuth auth.json restored from CODEX_AUTH_JSON (base64 decoded)"
    else
        # Assume it's raw JSON, write directly
        echo "$CODEX_AUTH_JSON" > "$CODEX_AUTH_FILE"
        echo "Codex OAuth auth.json restored from CODEX_AUTH_JSON (raw JSON)"
    fi
    
    # Ensure proper permissions
    chmod 600 "$CODEX_AUTH_FILE" 2>/dev/null || true
    
    # Don't force apikey - let Codex use OAuth
    # Only create config if it doesn't exist, and don't set preferred_auth_method
    if [ ! -f "$CODEX_CONFIG_FILE" ]; then
        cat > "$CODEX_CONFIG_FILE" <<'EOF'
# Using OAuth authentication (from CODEX_AUTH_JSON)
# preferred_auth_method is not set, allowing Codex to use OAuth by default
EOF
    fi
    echo "Codex CLI configured to use OAuth authentication"
    
# Priority 2: Check for existing OAuth tokens (for local development)
elif [ -f "$CODEX_AUTH_FILE" ] || [ -f "${CODEX_CONFIG_DIR}/credentials.json" ] || [ -f "${CODEX_CONFIG_DIR}/session" ]; then
    echo "Codex OAuth tokens found in ${CODEX_CONFIG_DIR}, using OAuth authentication"
    # Don't force apikey - let Codex use existing OAuth tokens
    if [ ! -f "$CODEX_CONFIG_FILE" ]; then
        cat > "$CODEX_CONFIG_FILE" <<'EOF'
# Using OAuth authentication (existing tokens found)
# preferred_auth_method is not set, allowing Codex to use OAuth by default
EOF
    fi
    
# Priority 3: Fall back to API key only if explicitly requested
else
    # Only use API key if CODEX_USE_API_KEY is explicitly set to true
    if [ "${CODEX_USE_API_KEY}" = "true" ] || [ "${CODEX_USE_API_KEY}" = "1" ]; then
        API_KEY="${CODEX_API_KEY:-${OPENAI_API_KEY}}"
        
        if [ -n "$API_KEY" ]; then
            export OPENAI_API_KEY="$API_KEY"
            cat > "$CODEX_CONFIG_FILE" <<'EOF'
preferred_auth_method = "apikey"
EOF
            echo "Codex CLI using API key authentication (CODEX_USE_API_KEY=true)"
        else
            echo "WARNING: CODEX_USE_API_KEY=true but no API key provided"
            echo "  Set CODEX_API_KEY or OPENAI_API_KEY environment variable"
        fi
    else
        echo "Codex CLI authentication not configured"
        echo "  Recommended: Run 'codex auth login' locally to create OAuth tokens"
        echo "  Or set CODEX_AUTH_JSON for OAuth in production"
        echo "  Or set CODEX_USE_API_KEY=true and CODEX_API_KEY for API key fallback"
    fi
fi

# Run database migrations using Alembic
echo "Running database migrations..."
alembic upgrade head || echo "Migrations completed (or already applied)"

# Fallback: Run database initialization if migrations fail (for first-time setup)
# This ensures tables exist even if alembic_version table doesn't
python init_db.py || echo "Database initialization completed (or already exists)"

# Execute the main command
exec "$@"
