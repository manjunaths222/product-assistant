# Product Assistant API

Product Assistant API with Agentic AI integration and Codex Product Assistant backend.

## Features

- **Project Management**: Register GitHub repositories and manage projects
- **Recipe Management**: List and query recipes (features) in projects
- **Feature Analysis**: Analyze codebase to return high-level design and feature details
- **Feasibility Assessment**: Analyze new requirements for technical feasibility, risks, and estimates

## Architecture

- **Backend**: Python FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **AI Integration**: 
  - Gemini API for LLM operations
  - Codex as agent tool (similar to jira-planbot)
- **Workflow**: LangGraph for orchestrating analysis workflows

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

#### Option A: Using PostgreSQL (Recommended)

**Install PostgreSQL:**

- **macOS** (using Homebrew):
  ```bash
  brew install postgresql@15
  brew services start postgresql@15
  ```
  
  **Note:** After installing via Homebrew, `psql` may not be in your PATH. Use one of these options:
  
  **Option 1: Use full path (recommended for one-time setup):**
  ```bash
  # For Apple Silicon (M1/M2/M3 Macs)
  /opt/homebrew/opt/postgresql@15/bin/psql -U postgres
  
  # For Intel Macs
  /usr/local/opt/postgresql@15/bin/psql -U postgres
  ```
  
  **Option 2: Add to PATH permanently:**
  ```bash
  # Add to your ~/.zshrc (for zsh) or ~/.bash_profile (for bash)
  echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
  source ~/.zshrc
  
  # Then you can use psql directly
  psql -U postgres
  ```

- **Linux** (Ubuntu/Debian):
  ```bash
  sudo apt-get update
  sudo apt-get install postgresql postgresql-contrib
  sudo systemctl start postgresql
  ```

- **Windows**: Download and install from [PostgreSQL official website](https://www.postgresql.org/download/windows/)

**Create Database:**

**For macOS with Homebrew (most common case):**

Homebrew PostgreSQL uses your macOS username as the superuser (not "postgres"). Use your username:

```bash
# Connect using your macOS username (replace 'yml' with your actual username)
psql -U yml -d postgres

# Or with full path if psql is not in PATH:
/opt/homebrew/opt/postgresql@15/bin/psql -U yml -d postgres

# Create database
CREATE DATABASE product_assistant;

# Exit psql
\q
```

**For Linux/Windows (standard PostgreSQL installation):**

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE product_assistant;

# Create user (optional, if not using default postgres user)
CREATE USER product_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE product_assistant TO product_user;

# Exit psql
\q
```

**Alternative: Create postgres role on macOS (if you prefer using 'postgres' user):**

If you want to use the standard "postgres" user on macOS:

```bash
# Create the postgres superuser role
/opt/homebrew/opt/postgresql@15/bin/createuser -s postgres

# Then you can use:
psql -U postgres
```

**Initialize Database Tables:**

```bash
# Set DATABASE_URL environment variable (or configure in .env file)
# For macOS with Homebrew (using your username, no password by default):
export DATABASE_URL="postgresql://yml@localhost:5432/product_assistant"

# For Linux/Windows (using postgres user):
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/product_assistant"

# Run database initialization script
python init_db.py
```

The `init_db.py` script will create all necessary tables:
- `projects` - Project information
- `recipes` - Recipe/feature information
- `chats` - Chat sessions for follow-up conversations

#### Option B: Using SQLite (Development Only)

For quick local development, you can use SQLite:

```bash
# Set DATABASE_URL to use SQLite
export DATABASE_URL="sqlite:///./product_assistant.db"

# Initialize database
python init_db.py
```

**Note:** SQLite is not recommended for production. Use PostgreSQL for production deployments.

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
# For macOS with Homebrew (use your username, no password by default):
DATABASE_URL=postgresql://yml@localhost:5432/product_assistant

# For Linux/Windows (use postgres user with password):
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/product_assistant

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODEL=gemini-2.5-pro

# Codex API Configuration
CODEX_API_KEY=your_codex_api_key_here
CODEX_MODEL=gpt-5-codex
CODEX_FALLBACK_MODEL=gpt-5

# Git Configuration
GIT_REPO_BASE_PATH=/tmp/product-assistant-repos
GIT_BRANCH=main
```

### 4. Run the Application

**Option 1: Using Python directly:**
```bash
python main.py
```

**Option 2: Using uvicorn (recommended for development):**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Projects

- `POST /projects` - Register a GitHub repository and create a project
- `GET /projects` - List all projects
- `GET /projects/{project_id}` - Get a specific project
- `POST /projects/{project_id}/feasibility` - Analyze feasibility of a new requirement

### Recipes

- `POST /recipes` - Create a new recipe for a project
- `GET /recipes` - List all recipes (optionally filter by project_id)
- `GET /recipes/{recipe_id}` - Get a specific recipe
- `POST /recipes/{recipe_id}/query` - Query for feature details

### Chats

- `POST /chats/{chat_id}/message` - Send a message in a chat session (for follow-up questions)
- `GET /chats/{chat_id}/history` - Get conversation history for a chat

### Health

- `GET /health` - Health check endpoint

## Usage

### Register a Project

```bash
# Project ID is auto-generated (UUID) if not provided
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "github_repo": "https://github.com/user/repo.git",
    "description": "My project description"
  }'

# Or provide a custom project_id
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-custom-project-id",
    "github_repo": "https://github.com/user/repo.git",
    "description": "My project description"
  }'
```

### Create a Recipe

```bash
curl -X POST "http://localhost:8000/recipes" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-project",
    "recipe_name": "User Authentication",
    "description": "User authentication feature"
  }'
```

### Query Feature Details

```bash
curl -X POST "http://localhost:8000/recipes/1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does the authentication feature work?"
  }'
```

### Analyze Feasibility

```bash
curl -X POST "http://localhost:8000/projects/my-project/feasibility" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "Add user authentication with OAuth2",
    "context": "Need to support Google and GitHub OAuth providers"
  }'
```

## Configuration

The application reads configuration from environment variables (see `.env.example`). Key configurations:

- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_API_KEY`: Gemini API key for LLM operations
- `CODEX_API_KEY`: Codex API key for code analysis
- `GIT_REPO_BASE_PATH`: Base path for cloning repositories

## Deployment on Render

The application is configured for deployment on Render using `render.yaml`.

### Environment Variables

Environment variables set in Render (via dashboard or `render.yaml`) are automatically passed to the Docker container and available to all processes, including the entrypoint script.

**Required environment variables:**
- `GEMINI_API_KEY`: Your Gemini API key (set in Render dashboard)
- `CODEX_API_KEY`: Your OpenAI API key (set in Render dashboard, used for Codex CLI authentication)

**Note:** `CODEX_API_KEY` is marked as `sync: false` in `render.yaml`, so it must be set manually in the Render dashboard if not already configured.

The service will automatically:
- Authenticate Codex CLI using the `CODEX_API_KEY` environment variable on container startup (via `docker-entrypoint.sh`)
- Connect to the PostgreSQL database configured in `render.yaml`
- Start the FastAPI server

## Database Schema

The application uses SQLAlchemy ORM with the following tables:

- **projects**: Stores project information
  - `id`: Primary key
  - `project_id`: Unique project identifier
  - `github_repo`: GitHub repository URL
  - `description`: Project description
  - `created_at`, `updated_at`: Timestamps

- **recipes**: Stores recipe/feature information
  - `id`: Primary key
  - `project_id`: Foreign key to projects
  - `recipe_name`: Name of the recipe/feature
  - `description`: Recipe description
  - `created_at`, `updated_at`: Timestamps

- **chats**: Stores chat sessions for follow-up conversations
  - `id`: Primary key
  - `project_id`: Foreign key to projects (optional)
  - `recipe_id`: Foreign key to recipes (optional)
  - `analysis_type`: Type of analysis ('feasibility' or 'feature')
  - `analysis_context`: Original analysis context
  - `conversation_history`: JSON string of conversation messages
  - `created_at`, `updated_at`: Timestamps

### Database Migrations

The application uses SQLAlchemy's `create_all()` to automatically create tables on startup. For production, consider using Alembic for database migrations:

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

**Manual Migration Scripts:**

If you need to add new columns to existing tables, migration scripts are provided:

```bash
# Add repo_path column to projects table (if upgrading from older version)
python migrate_add_repo_path.py
```

**Alternative: Direct SQL Migration**

You can also run SQL directly:

```sql
-- Connect to your database
psql -U yml -d product_assistant

-- Add repo_path column
ALTER TABLE projects ADD COLUMN repo_path VARCHAR(1000);

-- Update existing rows (adjust path as needed)
UPDATE projects SET repo_path = '/tmp/product-assistant-repos/' || project_id WHERE repo_path IS NULL;

-- Make column NOT NULL
ALTER TABLE projects ALTER COLUMN repo_path SET NOT NULL;
```

## Troubleshooting

### Database Connection Issues

**Error: "could not connect to server"**
- Ensure PostgreSQL is running: `sudo systemctl status postgresql` (Linux) or `brew services list` (macOS)
- Verify DATABASE_URL in your `.env` file matches your PostgreSQL configuration
- Check if PostgreSQL is listening on the correct port (default: 5432)

**Error: "database does not exist"**
- Create the database: `createdb product_assistant` or use psql to create it
- Verify the database name in DATABASE_URL matches the created database

**Error: "permission denied"**
- Ensure the database user has proper permissions
- For PostgreSQL, grant privileges: `GRANT ALL PRIVILEGES ON DATABASE product_assistant TO your_user;`

### Table Creation Issues

If tables are not created automatically:
```bash
# Manually run the initialization script
python init_db.py
```

### API Key Issues

- Ensure `GEMINI_API_KEY` and `CODEX_API_KEY` are set in your `.env` file
- Verify API keys are valid and have proper permissions

## Notes

- The application uses Codex terminal runner (similar to jira-planbot) for codebase analysis
- LangGraph workflows orchestrate the analysis process
- Repositories are cloned to `GIT_REPO_BASE_PATH/{project_id}`
- Chat sessions are automatically created after each analysis, allowing users to ask follow-up questions
- All responses are written in business-friendly language for product managers (no technical jargon or code details)

