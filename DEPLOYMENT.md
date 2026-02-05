# Deployment Guide - Render

This guide covers deploying the Product Assistant API to Render.com.

## Prerequisites

1. **GitHub Account** - Your code should be in a GitHub repository
2. **Render Account** - Sign up at [render.com](https://render.com) (free with GitHub)
3. **API Keys**:
   - `GEMINI_API_KEY` - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - `CODEX_API_KEY` - Your OpenAI/Codex API key

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
   CODEX_API_KEY=<your-codex-api-key>
   ```

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

### 2. Test API Endpoints

```bash
# Health check
curl https://product-assistant-api.onrender.com/health

# List projects
curl https://product-assistant-api.onrender.com/projects

# API Documentation
open https://product-assistant-api.onrender.com/docs
```

### 3. Monitor Logs

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
- Verify `init_db.py` runs successfully (check logs)
- Ensure API keys are valid
- Check application logs for specific errors

### API Keys Not Working

**Error: "Invalid API key"**
- Verify API keys are set correctly in environment variables
- Check for extra spaces in environment variable values
- Ensure API keys have proper permissions
- Verify API key quotas are not exceeded

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
