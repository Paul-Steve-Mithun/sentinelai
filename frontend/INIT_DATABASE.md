# 🚀 Initialize Database Locally (No Shell Access Needed!)

Since Render Shell is premium, we'll initialize the database from your local machine.

## Step 1: Get Your Database URL

1. Go to **Render Dashboard**: https://dashboard.render.com
2. Click on **Databases** (left sidebar)
3. Click on your database: **`sentinelai-db`**
4. Scroll down to **"Connections"**
5. Copy the **"External Database URL"** (starts with `postgres://`)

It looks like:
```
postgres://sentinelai:PASSWORD@dpg-xxxxx.oregon-postgres.render.com/sentinelai
```

## Step 2: Configure Local Backend

1. Open `backend/.env.local` (I just created it)
2. Replace `your_postgres_url_here` with your External Database URL
3. Save the file

## Step 3: Rename .env.local to .env

```bash
cd backend
# Backup your current .env if it exists
mv .env .env.backup
# Use the cloud database config
mv .env.local .env
```

Or just copy the DATABASE_URL into your existing `backend/.env`

## Step 4: Run Initialization Scripts

```bash
cd backend
python scripts/data_generator.py
python scripts/train_model.py
```

**Expected output:**
```
✅ Created 20 employees
✅ Generated 500+ behavioral events
✅ Calculated behavioral fingerprints
✅ Model trained successfully
✅ Model saved to models/anomaly_detector.pkl
```

## Step 5: Verify Data

Check if data was created:

```bash
python -c "from database import SessionLocal; from models import Employee; db = SessionLocal(); print(f'Employees: {db.query(Employee).count()}'); db.close()"
```

Should output: `Employees: 20`

## Step 6: Test Backend API

Open in browser:
- https://sentinelai-backend-lue3.onrender.com/api/employees

Should see 20 employees!

---

## Alternative: Quick API Method

If the above doesn't work, I can create a simple initialization endpoint that you can call via browser:

1. I'll add a `/api/init` endpoint
2. You visit: https://sentinelai-backend-lue3.onrender.com/api/init
3. Database gets populated automatically

**Which method do you prefer?**
- A) Get database URL and run scripts locally
- B) I create an `/api/init` endpoint for you

Let me know! 🚀
