# Deployment Guide - Render

This guide covers deploying the Product Assistant API to Render.com.

## Prerequisites

1. **GitHub Account** - Your code should be in a GitHub repository
2. **Render Account** - Sign up at [render.com](https://render.com) (free with GitHub)
3. **API Keys**:
   - `GEMINI_API_KEY` - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - `CODEX_AUTH_JSON` - OAuth auth.json (base64-encoded) for Codex CLI (recommended, no quota limits)
     - Or `CODEX_USE_API_KEY=true` + `CODEX_API_KEY` for API key authentication (has quota limits)

## Render Free Tier

**Free Tier Includes:**
- 750 hours/month of free compute time
- Free PostgreSQL database (90 days, then $7/month)
- Automatic SSL certificates
- Custom domains

## Deployment Steps

### Step 1: Create PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `product-assistant-db`
   - **Plan**: Free (90 days)
   - **Region**: Choose closest to you (e.g., Oregon, Frankfurt)
   - **Database**: `product_assistant`
   - **User**: `yml` (or leave default)
4. Click **"Create Database"**
5. **Important**: Copy the **Internal Database URL** or **External Database URL** (you'll need it in Step 3)

### Step 2: Deploy Web Service

1. In Render Dashboard, click **"New"** → **"Web Service"**
2. **Connect GitHub**:
   - Click "Connect GitHub" if not already connected
   - Authorize Render to access your repositories
   - Select the `product-assistant` repository
3. **Configure Service**:
   - **Name**: `product-assistant-api`
   - **Region**: Same as your database
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty
   - **Environment**: `Docker`
   - **Dockerfile Path**: `Dockerfile`
   - **Docker Context**: `.`

### Step 3: Set Environment Variables

1. In your Web Service settings, go to **"Environment"** tab
2. Add the following environment variables:

   **Required:**
   ```
   DATABASE_URL=<your-postgres-connection-string-from-step-1>
   GEMINI_API_KEY=<your-gemini-api-key>
   CODEX_AUTH_JSON=<base64-encoded-auth-json>
   ```
   
   **To get CODEX_AUTH_JSON:**
   1. On your local machine, run: `codex auth login`
   2. Get the base64-encoded content: `cat ~/.codex/auth.json | base64`
   3. Copy the entire output and paste it as `CODEX_AUTH_JSON` value

   **Optional (with defaults):**
   ```
   HOST=0.0.0.0
   PORT=8000
   GEMINI_MODEL=gemini-2.5-flash
   GEMINI_FALLBACK_MODEL=gemini-2.5-pro
   CODEX_MODEL=gpt-5-codex
   CODEX_FALLBACK_MODEL=gpt-5
   GIT_REPO_BASE_PATH=/tmp/product-assistant-repos
   GIT_BRANCH=main
   ```
   
   **Alternative (API Key - has quota limits):**
   If you prefer API key instead of OAuth:
   ```
   CODEX_USE_API_KEY=true
   CODEX_API_KEY=<your-codex-api-key>
   ```

   **Example DATABASE_URL:**
   ```
   postgresql://yml:password@dpg-xxxxx.oregon-postgres.render.com:5432/product_assistant
   ```

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Build your Docker image
   - Deploy the service
   - Show build logs in real-time
3. Once deployed, your API will be available at:
   ```
   https://product-assistant-api.onrender.com
   ```

## Post-Deployment

### 1. Verify Database Initialization

Check that tables were created:

```bash
curl https://product-assistant-api.onrender.com/health
```

### 2. Database Migrations

**How Migrations Work in Deployment:**

The deployment uses **Alembic** for database schema migrations. Here's how it works:

1. **Automatic Migration on Deploy:**
   - Every time your service starts (including after each deployment), the `docker-entrypoint.sh` script automatically runs:
     ```bash
     alembic upgrade head
     ```
   - This applies any pending migrations to bring your database schema up to date
   - Migrations are **idempotent** - running them multiple times is safe

2. **Migration Tracking:**
   - Alembic creates an `alembic_version` table in your database
   - This table stores the current migration version
   - Alembic only applies migrations that haven't been run yet

3. **Migration Process:**
   ```
   Local Development → Commit Migration → Push to GitHub → Render Deploys → Auto-Run Migrations
   ```

4. **Creating New Migrations (Local Development):**
   ```bash
   # After making model changes, create a new migration
   alembic revision --autogenerate -m "description_of_changes"
   
   # Review the generated migration file in alembic/versions/
   # Then commit and push - it will auto-apply on next deployment
   ```

5. **Manual Migration (If Needed):**
   If you need to manually run migrations on the deployed database:
   ```bash
   # Connect to your Render service via SSH (if available) or use Render Shell
   alembic upgrade head
   ```

6. **Rolling Back (Emergency):**
   ```bash
   # Rollback one migration
   alembic downgrade -1
   
   # Rollback to specific revision
   alembic downgrade <revision_id>
   ```

**Important Notes:**
- ✅ Migrations run automatically on every deployment
- ✅ Safe to run multiple times (idempotent)
- ✅ Tracks migration history in `alembic_version` table
- ⚠️ Always test migrations locally before deploying
- ⚠️ Backup database before major schema changes

### 3. Test API Endpoints

```bash
# Health check
curl https://product-assistant-api.onrender.com/health

# List projects
curl https://product-assistant-api.onrender.com/projects

# API Documentation
open https://product-assistant-api.onrender.com/docs
```

### 4. Monitor Logs

- Go to Render Dashboard → Your Service → **"Logs"** tab
- View real-time logs and errors

## Important Notes

### Free Tier Limitations

1. **Cold Starts**: 
   - Services spin down after 15 minutes of inactivity
   - First request after spin-down may take 30-60 seconds
   - Solution: Use the included GitHub Actions workflow to ping your service every 10 minutes

2. **Database**:
   - Free PostgreSQL is available for 90 days
   - After 90 days: $7/month
   - Consider upgrading if you need persistent database

3. **Resource Limits**:
   - Free tier has CPU/RAM limits
   - May not handle high traffic well
   - Consider upgrading for production use

### Keeping Service Alive

The repository includes a GitHub Actions workflow (`.github/workflows/keep-alive.yml`) that pings your service every 10 minutes to prevent spin-down.

**To use it:**

1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Add a new secret:
   - **Name**: `RENDER_URL`
   - **Value**: `https://your-app-name.onrender.com`
3. The workflow will automatically run every 10 minutes

**Alternative:** Use [cron-job.org](https://cron-job.org) (free) to ping your service:
- URL: `https://your-app-name.onrender.com/health`
- Frequency: Every 10 minutes

## Troubleshooting

### Database Connection Issues

**Error: "could not connect to server"**
- Verify `DATABASE_URL` is set correctly in environment variables
- Check database is running in Render Dashboard
- Ensure you're using the correct connection string (Internal vs External)
- For external connections, ensure your database allows external connections

**Error: "database does not exist"**
- Verify database name in `DATABASE_URL` matches the created database
- Check database status in Render Dashboard

### Build Failures

**Error: "Docker build failed"**
- Check Dockerfile syntax
- Verify all dependencies in `requirements.txt`
- Check build logs in Render Dashboard for specific errors

**Error: "Module not found"**
- Ensure all dependencies are listed in `requirements.txt`
- Check Python version compatibility

### Service Not Starting

**Error: "Application failed to start"**
- Check environment variables are set correctly
- Verify migrations run successfully (check logs for `alembic upgrade head`)
- Ensure API keys are valid
- Check application logs for specific errors

**Error: "Migration failed" or "alembic_version table not found"**
- First deployment: The `init_db.py` fallback will create tables if migrations fail
- Subsequent deployments: Check that `DATABASE_URL` is correct
- Verify database connection is working
- Check migration files are present in `alembic/versions/`

### Codex Authentication Issues

**Error: "Invalid API key" or "Authentication failed"**
- **For OAuth (Recommended):**
  - Verify `CODEX_AUTH_JSON` is set correctly (base64-encoded auth.json)
  - Check that the base64 encoding is correct (no extra spaces or line breaks)
  - Ensure the auth.json was generated from `codex auth login` on your local machine
  - Check container logs for "Codex OAuth auth.json restored" message
- **For API Key:**
  - Verify `CODEX_USE_API_KEY=true` and `CODEX_API_KEY` are set correctly
  - Check for extra spaces in environment variable values
  - Ensure API keys have proper permissions
  - Verify API key quotas are not exceeded (OAuth has no quota limits)

**Getting CODEX_AUTH_JSON:**
```bash
# On your local machine
codex auth login
cat ~/.codex/auth.json | base64
# Copy the entire output and paste as CODEX_AUTH_JSON in Render
```

## Updating Your Deployment

Render automatically deploys on every push to your main branch. To manually trigger a deployment:

1. Go to Render Dashboard → Your Service
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

## Custom Domain (Optional)

1. Go to Render Dashboard → Your Service → Settings
2. Scroll to **"Custom Domains"**
3. Add your domain
4. Follow DNS configuration instructions

## Next Steps

1. Set up monitoring/alerting
2. Configure custom domain (optional)
3. Consider upgrading if you need more resources
4. Set up CI/CD for automated testing before deployment
