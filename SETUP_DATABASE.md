# Database Setup Guide

## Your Render PostgreSQL Database

Based on your connection details, here's how to configure your database:

### Connection String Format

Your full connection string should be:
```
postgresql://yml:m2M2pmwLeYTFRVvdFJpd0imaawhHvUE4@dpg-d62admvfte5s738h79e0-a.oregon-postgres.render.com:5432/product_assistant
```

### For Local Development (.env file)

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://yml:m2M2pmwLeYTFRVvdFJpd0imaawhHvUE4@dpg-d62admvfte5s738h79e0-a.oregon-postgres.render.com:5432/product_assistant

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

### For Render Deployment

When deploying to Render, set the `DATABASE_URL` environment variable in your Web Service settings:

1. Go to your Render Web Service dashboard
2. Navigate to "Environment" tab
3. Add or update `DATABASE_URL`:
   ```
   postgresql://yml:m2M2pmwLeYTFRVvdFJpd0imaawhHvUE4@dpg-d62admvfte5s738h79e0-a.oregon-postgres.render.com:5432/product_assistant
   ```

### Testing the Connection

You can test the connection using psql:

```bash
PGPASSWORD=m2M2pmwLeYTFRVvdFJpd0imaawhHvUE4 psql -h dpg-d62admvfte5s738h79e0-a.oregon-postgres.render.com -U yml product_assistant
```

Or using the connection string:

```bash
psql "postgresql://yml:m2M2pmwLeYTFRVvdFJpd0imaawhHvUE4@dpg-d62admvfte5s738h79e0-a.oregon-postgres.render.com:5432/product_assistant"
```

### Initialize Database Tables

After setting up the connection, initialize the database tables:

```bash
# Make sure DATABASE_URL is set in your .env file or environment
python init_db.py
```

Or the tables will be created automatically when you start the application.

### Security Note

⚠️ **Important**: The connection string contains your database password. Never commit it to version control!

- Make sure `.env` is in your `.gitignore` (already added)
- Use environment variables in production
- Consider rotating your password if it was ever exposed

