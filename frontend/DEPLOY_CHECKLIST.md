# SentinelAI - Quick Deployment Checklist

## ✅ Pre-Deployment Checklist

- [x] PostgreSQL support added to `database.py`
- [x] `psycopg2-binary` added to requirements.txt
- [x] `gunicorn` added for production server
- [x] `Procfile` created for deployment
- [x] `render.yaml` created for automatic setup
- [x] Deployment guide created

## 🚀 Deploy in 3 Steps

### 1. Push to GitHub

```bash
cd c:\Users\drums\OneDrive\Desktop\DakshaaT26\SentinelAI\sentinelai

# Initialize git (if not already done)
git init
git add .
git commit -m "Ready for deployment"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/sentinelai.git
git branch -M main
git push -u origin main
```

### 2. Deploy on Render

1. Go to https://render.com and sign up
2. Click "New" → "Blueprint"
3. Connect your GitHub repo
4. Render will detect `render.yaml` and create:
   - ✅ PostgreSQL database (free)
   - ✅ Backend API service (free)
5. Click "Apply" and wait 5-10 minutes

### 3. Get Your URL

After deployment completes:
- Your backend URL: `https://sentinelai-backend-XXXX.onrender.com`
- Test it: `https://your-url.onrender.com/docs`

## 📱 Update Agent Configuration

On friend's laptop, edit `agent/config.json`:

```json
{
  "backend_url": "https://sentinelai-backend-XXXX.onrender.com",
  "collection_interval": 30
}
```

## 🌐 Update Frontend

Edit `.env`:
```
VITE_API_URL=https://sentinelai-backend-XXXX.onrender.com
```

## 🎯 Test Deployment

```bash
# Health check
curl https://your-url.onrender.com/health

# API docs (open in browser)
https://your-url.onrender.com/docs
```

## 📊 Initialize Data

After deployment, generate demo data:

```bash
# Option 1: Via API
curl -X POST https://your-url.onrender.com/api/ml/train

# Option 2: Via Render Shell
# Go to Render dashboard → Shell → Run:
cd backend
python scripts/data_generator.py
python scripts/detect_anomalies.py
```

## ⚡ Quick Troubleshooting

**Build fails?**
- Check Python version in render.yaml (should be 3.11+)
- Verify all files are committed to git

**Database connection error?**
- Wait for database to finish provisioning
- Check DATABASE_URL is set in environment variables

**Slow first request?**
- Free tier services sleep after 15 min inactivity
- First request wakes it up (30-60 seconds)

---

**Full documentation**: See `DEPLOYMENT.md` for detailed guide

**Ready to demo!** 🎉
