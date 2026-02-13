# SentinelAI - Cloud Deployment Guide

## 🚀 Deploy to Render (Recommended)

### Prerequisites
- GitHub account
- Render account (free tier available)

### Step-by-Step Deployment

#### 1. Push Code to GitHub

```bash
cd c:\Users\drums\OneDrive\Desktop\DakshaaT26\SentinelAI\sentinelai
git init
git add .
git commit -m "Initial commit - SentinelAI"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sentinelai.git
git push -u origin main
```

#### 2. Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

#### 3. Deploy Backend

**Option A: Using render.yaml (Automatic)**

1. Click "New" → "Blueprint"
2. Connect your GitHub repository
3. Render will detect `render.yaml` and set up everything automatically
4. Click "Apply" - this creates:
   - PostgreSQL database (free tier)
   - Web service (backend API)
   - Environment variables

**Option B: Manual Setup**

1. **Create PostgreSQL Database:**
   - Click "New" → "PostgreSQL"
   - Name: `sentinelai-db`
   - Database: `sentinelai`
   - User: `sentinelai`
   - Region: Choose closest to you
   - Plan: Free
   - Click "Create Database"
   - **Copy the Internal Database URL** (starts with `postgres://`)

2. **Create Web Service:**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Name: `sentinelai-backend`
   - Region: Same as database
   - Branch: `main`
   - Root Directory: `backend`
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
   - Plan: Free

3. **Add Environment Variables:**
   - Click "Environment" tab
   - Add:
     - `DATABASE_URL` = (paste the Internal Database URL from step 1)
     - `CORS_ORIGINS` = `*`
   - Click "Save Changes"

#### 4. Wait for Deployment
- Render will build and deploy (5-10 minutes)
- Watch the logs for any errors
- Once deployed, you'll get a URL like: `https://sentinelai-backend.onrender.com`

#### 5. Test Your Deployment

```bash
# Test health endpoint
curl https://your-app.onrender.com/health

# Test API docs
# Open in browser: https://your-app.onrender.com/docs
```

#### 6. Update Agent Configuration

On your friend's laptop, edit `agent/config.json`:

```json
{
  "backend_url": "https://your-app.onrender.com",
  "collection_interval": 30
}
```

#### 7. Update Frontend Configuration

Edit `sentinelai/.env`:

```
VITE_API_URL=https://your-app.onrender.com
```

Then rebuild frontend:
```bash
npm run build
```

---

## 🌐 Deploy Frontend (Optional)

### Option 1: Vercel (Recommended for React)

```bash
npm install -g vercel
cd sentinelai
vercel
```

### Option 2: Render Static Site

1. Click "New" → "Static Site"
2. Connect repository
3. Build Command: `npm run build`
4. Publish Directory: `dist`

---

## 🐛 Troubleshooting

### Database Connection Errors
- Verify `DATABASE_URL` environment variable is set
- Check database is in same region as web service
- Ensure URL starts with `postgresql://` (Render auto-converts)

### Build Failures
- Check Python version (should be 3.11+)
- Verify all dependencies in `requirements.txt`
- Check build logs for specific errors

### CORS Errors
- Ensure `CORS_ORIGINS` includes your frontend URL
- Or set to `*` for development

### Slow First Request
- Free tier services sleep after inactivity
- First request may take 30-60 seconds
- Subsequent requests are fast

---

## 📊 Post-Deployment

### Initialize Database

After first deployment, run data generator:

```bash
# SSH into Render (or use Render Shell)
python scripts/data_generator.py
```

Or use the API:
```bash
curl -X POST https://your-app.onrender.com/api/ml/train
```

### Monitor Your App

- **Render Dashboard**: View logs, metrics, deployments
- **API Docs**: `https://your-app.onrender.com/docs`
- **Health Check**: `https://your-app.onrender.com/health`

---

## 💡 Pro Tips

1. **Custom Domain**: Add your own domain in Render settings
2. **Auto-Deploy**: Enable auto-deploy on git push
3. **Environment Secrets**: Use Render's secret management
4. **Monitoring**: Set up Render's built-in monitoring
5. **Scaling**: Upgrade to paid tier for better performance

---

## 🎯 For Hackathon Demo

1. **Share the URL** with judges
2. **Show live monitoring** - agent on friend's laptop
3. **Demonstrate isolation** - real network disconnect
4. **API Documentation** - show `/docs` endpoint
5. **Production-ready** - hosted on real cloud infrastructure

Your app is now accessible from anywhere in the world! 🌍
