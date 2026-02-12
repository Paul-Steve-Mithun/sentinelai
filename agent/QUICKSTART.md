# Phase 1: Monitoring Agent - Quick Start Guide

## 🎯 What You Have Now

### Agent Files Created:
- `agent/sentinel_agent.py` - Main monitoring agent
- `agent/config.json` - Configuration file
- `agent/requirements.txt` - Dependencies
- `agent/README.md` - Full documentation

### Backend API Created:
- `/api/agent/register` - Register new agent
- `/api/agent/{id}/status` - Check isolation status
- `/api/agent/events/batch` - Receive events
- `/api/agent/{id}/isolate` - Isolate from network
- `/api/agent/{id}/restore` - Restore network

## 🚀 Quick Setup (5 Minutes)

### Step 1: Update Backend
The backend has been updated with agent routes. **Restart your backend server**:

```powershell
# In backend terminal (Ctrl+C to stop current server)
uvicorn main:app --reload
```

### Step 2: Install Agent on Friend's Laptop

**Copy the `agent` folder** to your friend's laptop, then:

```powershell
cd agent
pip install -r requirements.txt
```

### Step 3: Configure Backend URL

Edit `agent/config.json` and replace `localhost` with **your laptop's IP address**:

```json
{
  "backend_url": "http://YOUR_IP_ADDRESS:8000",
  "collection_interval": 30
}
```

**To find your IP**: Run `ipconfig` and look for IPv4 Address

### Step 4: Run the Agent

**On friend's laptop** (requires Administrator):

```powershell
# Right-click PowerShell -> Run as Administrator
python sentinel_agent.py
```

The agent will:
1. Register with your backend
2. Start collecting events every 30 seconds
3. Send events to your dashboard
4. Check for isolation commands

## 📊 What Happens Next

1. **Agent collects events**: Login, file access, network connections
2. **Events sent to backend**: Every 30 seconds
3. **ML model analyzes**: Real-time anomaly detection
4. **Dashboard updates**: See live activity
5. **Anomalies trigger alerts**: High-risk behavior detected
6. **You can isolate**: Click button to disconnect from network

## 🎬 Demo Flow

1. **Show agent running** on friend's laptop
2. **Open your dashboard** - see real-time events
3. **Trigger anomaly** - access unusual files, connect to weird ports
4. **Show detection** - anomaly appears in dashboard
5. **Click "Isolate"** - friend's laptop loses network
6. **Click "Restore"** - network comes back

## ⚠️ Important Notes

- **Admin privileges required** for network isolation
- **Same network**: Both laptops should be on same WiFi/LAN
- **Firewall**: May need to allow port 8000
- **Consent**: Only monitor with permission!

## 🐛 Troubleshooting

**Agent won't connect?**
- Check backend is running
- Verify IP address in config.json
- Test: `curl http://YOUR_IP:8000/health`

**No events in dashboard?**
- Check agent terminal for errors
- Verify employee_id in config.json
- Check backend logs

**Isolation not working?**
- Run agent as Administrator
- Check PowerShell execution policy

## ✅ Success Indicators

- Agent shows "✅ Agent registered successfully!"
- Agent shows "✅ Sent X events to backend"
- Dashboard shows new employee
- Events appear in employee profile

---

**Ready for Phase 2?** Let me know when this is working and I'll add:
- WebSocket for real-time streaming
- UI isolation button
- Live event feed
- Network status indicator
