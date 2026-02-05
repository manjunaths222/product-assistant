FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for git repos
RUN mkdir -p /tmp/product-assistant-repos

# Expose port
EXPOSE 8000

# Run database initialization and start server
# Note: main.py also creates tables on startup, but we run init_db.py explicitly for clarity
CMD python init_db.py || echo "Database initialization completed (or already exists)" && uvicorn main:app --host 0.0.0.0 --port 8000

