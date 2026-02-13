# 🚀 SentinelAI - Final Setup Steps

## ✅ What's Done

- ✅ Backend deployed: https://sentinelai-backend-lue3.onrender.com
- ✅ Frontend configured: `.env` updated
- ✅ Agent configured: `agent/config.json` updated
- ✅ Backend is healthy and running

## 📊 Initialize Database (REQUIRED)

Your PostgreSQL database is empty. You need to populate it with demo data.

### Option 1: Render Shell (Recommended - 2 minutes)

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Select your service**: `sentinelai-backend`
3. **Click "Shell" tab** (top right)
4. **Run these commands**:

```bash
cd backend
python scripts/data_generator.py
python scripts/train_model.py
```

**Expected output:**
- ✅ Created 20 employees
- ✅ Generated ~500 behavioral events
- ✅ Trained anomaly detection model
- ✅ Model saved successfully

### Option 2: Local Script Upload (Alternative)

If Render Shell doesn't work, you can run locally and upload:

```bash
# In your local backend folder
cd backend
python scripts/data_generator.py
python scripts/train_model.py
```

Then the database will be populated via your DATABASE_URL environment variable.

---

## 🌐 Test Your Deployment

### 1. Test Backend API

Open in browser:
- **API Docs**: https://sentinelai-backend-lue3.onrender.com/docs
- **Health Check**: https://sentinelai-backend-lue3.onrender.com/health
- **Employees**: https://sentinelai-backend-lue3.onrender.com/api/employees

After initialization, you should see 20 employees in the employees endpoint.

### 2. Test Frontend

Your frontend is already configured! Just **restart the dev server**:

```bash
# Stop current server (Ctrl+C in the terminal running npm run dev)
# Then restart:
npm run dev
```

Open http://localhost:5173 - you should see:
- ✅ Dashboard with statistics
- ✅ Employee list
- ✅ Anomaly detections
- ✅ Charts and visualizations

---

## 🤖 Set Up Agent on Friend's Laptop

### Step 1: Copy Agent Folder

Copy the entire `agent/` folder to your friend's laptop.

### Step 2: Install Dependencies

On friend's laptop:

```bash
cd agent
pip install -r requirements.txt
```

### Step 3: Run Agent

**Important**: Run as Administrator (for network isolation feature)

```powershell
# Right-click PowerShell → Run as Administrator
cd agent
python sentinel_agent.py
```

**First run output:**
```
📝 First time setup - registering with backend...
✅ Agent registered successfully! Employee ID: 21
🚀 SentinelAI Agent Started
```

The agent will:
- ✅ Register with your backend
- ✅ Collect events every 30 seconds
- ✅ Send data to your cloud backend
- ✅ Check for isolation commands

### Step 4: Verify Agent is Working

1. **Check agent terminal** - should show "✅ Sent X events to backend"
2. **Check your dashboard** - new employee should appear
3. **Check backend logs** on Render - should show incoming events

---

## 🎯 Demo Flow for Hackathon

1. **Show Dashboard**: Live monitoring of all employees
2. **Show Agent Running**: On friend's laptop collecting real data
3. **Trigger Anomaly**: 
   - Access unusual files
   - Connect to unusual ports
   - Run suspicious processes
4. **Show Detection**: Anomaly appears in dashboard with:
   - Risk score
   - SHAP explanation
   - MITRE ATT&CK mapping
   - Mitigation strategies
5. **Demonstrate Isolation**: Click isolate button (Phase 2 - coming next!)

---

## 🐛 Troubleshooting

### Backend Issues

**"Internal Server Error" on /api/ml/train**
- Database not initialized yet - use Render Shell method above

**"No employees found"**
- Run data_generator.py first

### Frontend Issues

**"Network Error" or "Failed to fetch"**
- Check `.env` has correct URL
- Restart dev server after changing `.env`
- Check CORS is enabled (already configured)

### Agent Issues

**"Failed to register"**
- Check backend URL in `agent/config.json`
- Test backend health: https://sentinelai-backend-lue3.onrender.com/health

**"No events being sent"**
- Check agent terminal for errors
- Verify internet connection
- Check backend logs on Render

---

## ✅ Success Checklist

- [ ] Database initialized (20 employees visible)
- [ ] Frontend shows dashboard with data
- [ ] Agent registered and sending events
- [ ] New employee appears in dashboard
- [ ] Anomalies are being detected

---

## 🚀 Next: Phase 2 (Optional)

Once everything is working, we can add:
- WebSocket for real-time updates
- UI isolation button
- Live event feed
- Network status indicator

**Let me know when database is initialized and I'll help with Phase 2!** 🎉
