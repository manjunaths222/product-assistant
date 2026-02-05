FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Node.js for Codex CLI
RUN apt-get update && apt-get install -y \
    git \
    postgresql-client \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Codex CLI globally
RUN npm i -g @openai/codex || echo "Codex CLI installation failed - will continue without it"

# Copy application code
COPY . .

# Copy and set permissions for entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create directory for git repos
RUN mkdir -p /tmp/product-assistant-repos

# Expose port
EXPOSE 8000

# Use entrypoint script to authenticate Codex and run commands
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command: start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

