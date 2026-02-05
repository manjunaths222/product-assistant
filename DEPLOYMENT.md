# Deployment Guide - Free Platforms

This guide covers deploying the Product Assistant API to free hosting platforms.

## Prerequisites

1. **GitHub Account** - Your code should be in a GitHub repository
2. **API Keys** - You'll need:
   - `GEMINI_API_KEY` - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - `CODEX_API_KEY` - Your OpenAI/Codex API key

## Free Deployment Options

### Option 1: Render (Recommended) ⭐

**Free Tier Includes:**
- 750 hours/month of free compute time
- Free PostgreSQL database (90 days, then $7/month)
- Automatic SSL certificates
- Custom domains

**Steps:**

1. **Sign up** at [render.com](https://render.com) (free with GitHub)

2. **Create PostgreSQL Database:**
   - Go to Dashboard → New → PostgreSQL
   - Name: `product-assistant-db`
   - Plan: Free (90 days)
   - Region: Choose closest to you
   - Click "Create Database"
   - Note the connection string (you'll use it later)

3. **Deploy Web Service:**
   - Go to Dashboard → New → Web Service
   - Connect your GitHub repository
   - Select the `product-assistant` repository
   - Configure:
     - **Name**: `product-assistant-api`
     - **Region**: Same as database
     - **Branch**: `main` (or your default branch)
     - **Root Directory**: Leave empty
     - **Environment**: `Docker`
     - **Dockerfile Path**: `Dockerfile`
     - **Docker Context**: `.`

4. **Set Environment Variables:**
   - In the Web Service settings, go to "Environment"
   - Add these variables:
     ```
     DATABASE_URL=<your-postgres-connection-string>
     HOST=0.0.0.0
     PORT=8000
     GEMINI_API_KEY=<your-gemini-api-key>
     GEMINI_MODEL=gemini-2.5-flash
     GEMINI_FALLBACK_MODEL=gemini-2.5-pro
     CODEX_API_KEY=<your-codex-api-key>
     CODEX_MODEL=gpt-5-codex
     CODEX_FALLBACK_MODEL=gpt-5
     GIT_REPO_BASE_PATH=/tmp/product-assistant-repos
     GIT_BRANCH=main
     ```

5. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - Your API will be available at: `https://product-assistant-api.onrender.com`

**Note:** Free tier services spin down after 15 minutes of inactivity. First request after spin-down may take 30-60 seconds.

---

### Option 2: Railway

**Free Tier Includes:**
- $5/month credit (enough for small apps)
- Free PostgreSQL database
- Automatic deployments from GitHub

**Steps:**

1. **Sign up** at [railway.app](https://railway.app) (free with GitHub)

2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `product-assistant` repository

3. **Add PostgreSQL Database:**
   - In your project, click "+ New"
   - Select "Database" → "Add PostgreSQL"
   - Railway automatically creates the database

4. **Configure Web Service:**
   - Railway should auto-detect the Dockerfile
   - If not, go to Settings → Source → Dockerfile Path: `Dockerfile`

5. **Set Environment Variables:**
   - Go to your web service → Variables
   - Add:
     ```
     DATABASE_URL=${{Postgres.DATABASE_URL}}
     HOST=0.0.0.0
     PORT=$PORT
     GEMINI_API_KEY=<your-gemini-api-key>
     GEMINI_MODEL=gemini-2.5-flash
     GEMINI_FALLBACK_MODEL=gemini-2.5-pro
     CODEX_API_KEY=<your-codex-api-key>
     CODEX_MODEL=gpt-5-codex
     CODEX_FALLBACK_MODEL=gpt-5
     GIT_REPO_BASE_PATH=/tmp/product-assistant-repos
     GIT_BRANCH=main
     ```
   - Note: `DATABASE_URL` uses Railway's variable reference syntax

6. **Deploy:**
   - Railway will automatically deploy on every push to main
   - Get your URL from the service settings

---

### Option 3: Fly.io

**Free Tier Includes:**
- 3 shared-cpu VMs with 256MB RAM each
- 3GB persistent volume storage
- 160GB outbound data transfer

**Note:** If you encounter connection errors with Fly.io CLI, see `FLY_TROUBLESHOOTING.md` for solutions. Since you already have a Render database, **Render is recommended** (see Option 1).

**Steps:**

1. **Install Fly CLI:**
   ```bash
   brew install flyctl
   # or
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign up and login:**
   ```bash
   fly auth signup
   fly auth login
   # If you get connection errors, try:
   fly auth login --web
   ```

3. **Create app:**
   ```bash
   fly launch
   ```
   - Follow prompts to create app
   - Don't deploy yet (we need to configure database first)

4. **Create PostgreSQL Database:**
   ```bash
   fly postgres create --name product-assistant-db
   ```
   - Note the connection string

5. **Attach Database:**
   ```bash
   fly postgres attach --app product-assistant-api product-assistant-db
   ```

6. **Set Secrets:**
   ```bash
   fly secrets set GEMINI_API_KEY=<your-gemini-api-key>
   fly secrets set CODEX_API_KEY=<your-codex-api-key>
   fly secrets set GEMINI_MODEL=gemini-2.5-flash
   fly secrets set GEMINI_FALLBACK_MODEL=gemini-2.5-pro
   fly secrets set CODEX_MODEL=gpt-5-codex
   fly secrets set CODEX_FALLBACK_MODEL=gpt-5
   fly secrets set GIT_REPO_BASE_PATH=/tmp/product-assistant-repos
   fly secrets set GIT_BRANCH=main
   ```

7. **Deploy:**
   ```bash
   fly deploy
   ```

8. **Get URL:**
   ```bash
   fly open
   ```

---

### Option 4: Supabase + Fly.io/Render

**Free Tier Includes:**
- Free PostgreSQL database (500MB, unlimited API requests)
- Can host FastAPI separately on Fly.io or Render

**Steps:**

1. **Create Supabase Project:**
   - Sign up at [supabase.com](https://supabase.com)
   - Create new project
   - Get connection string from Settings → Database

2. **Deploy FastAPI:**
   - Use any of the above methods (Render/Railway/Fly.io)
   - Set `DATABASE_URL` to your Supabase connection string
   - Format: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`

---

## Post-Deployment

### 1. Verify Database Initialization

Check that tables were created. You can use the health endpoint:
```bash
curl https://your-app-url.onrender.com/health
```

### 2. Test API Endpoints

```bash
# Health check
curl https://your-app-url.onrender.com/health

# List projects
curl https://your-app-url.onrender.com/projects

# API Documentation
open https://your-app-url.onrender.com/docs
```

### 3. Monitor Logs

- **Render**: Dashboard → Your Service → Logs
- **Railway**: Dashboard → Your Service → Deployments → View Logs
- **Fly.io**: `fly logs`

---

## Important Notes

### Free Tier Limitations

1. **Cold Starts**: Free tiers may spin down after inactivity
   - First request after inactivity may be slow (30-60 seconds)
   - Consider using a cron job to ping your service every 10 minutes

2. **Database Limits:**
   - Render: 90 days free, then $7/month
   - Railway: Included in $5 credit
   - Fly.io: Pay-as-you-go after free tier
   - Supabase: Free tier has 500MB limit

3. **Resource Limits:**
   - Free tiers have CPU/RAM limits
   - May not handle high traffic well

### Keeping Service Alive (Free Tiers)

For Render, you can use a free cron service to ping your API:

1. Use [cron-job.org](https://cron-job.org) (free)
2. Set up a job to ping: `https://your-app.onrender.com/health` every 10 minutes

Or use GitHub Actions:

```yaml
# .github/workflows/keep-alive.yml
name: Keep Alive
on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping service
        run: curl https://your-app.onrender.com/health
```

---

## Troubleshooting

### Database Connection Issues

- Verify `DATABASE_URL` is set correctly
- Check database is running (Render/Railway dashboards)
- Ensure database allows connections from your service IP

### Build Failures

- Check Dockerfile syntax
- Verify all dependencies in `requirements.txt`
- Check build logs in platform dashboard

### Service Not Starting

- Check environment variables are set
- Verify `init_db.py` runs successfully
- Check application logs

### API Keys Not Working

- Verify API keys are set correctly in environment variables
- Check API key permissions and quotas
- Ensure no extra spaces in environment variable values

---

## Cost Comparison

| Platform | Free Tier | Database | Best For |
|----------|-----------|----------|----------|
| **Render** | 750 hrs/month | 90 days free | Easiest setup |
| **Railway** | $5 credit/month | Included | Good balance |
| **Fly.io** | 3 VMs, 256MB each | Pay-as-you-go | More control |
| **Supabase** | Unlimited API | 500MB free | Database focus |

---

## Next Steps

1. Set up custom domain (optional, may require paid tier)
2. Configure monitoring/alerting
3. Set up CI/CD for automatic deployments
4. Consider upgrading if you need more resources

