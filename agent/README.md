# SentinelAI Monitoring Agent

## Overview
Lightweight monitoring agent that runs on target laptops to collect behavioral events and enable real-time threat detection.

## Features
- 🔍 **Real-time Event Collection**: Login, file access, network, process monitoring
- 📡 **Automatic Event Transmission**: Sends events to backend API
- 🚨 **Network Isolation**: Can isolate machine from network on command
- 💓 **Heartbeat Monitoring**: Regular status checks with backend
- ⚙️ **Configurable**: Adjust collection intervals and monitored resources

## Installation

### On the Monitored Laptop (Friend's Laptop)

1. **Copy the agent folder** to the target laptop

2. **Install dependencies**:
```powershell
cd agent
pip install -r requirements.txt
```

3. **Configure the backend URL** in `config.json`:
```json
{
  "backend_url": "http://YOUR_IP:8000",
  "collection_interval": 30
}
```

4. **Run the agent** (requires Administrator privileges for network isolation):
```powershell
# Right-click PowerShell -> Run as Administrator
python sentinel_agent.py
```

## First Run

On first run, the agent will:
1. Register with the backend
2. Receive an employee ID
3. Start collecting and sending events
4. Check for isolation commands every collection cycle

## Configuration

Edit `config.json` to customize:

- `backend_url`: Your SentinelAI backend URL
- `collection_interval`: Seconds between event collections (default: 30)
- `batch_size`: Number of events to send per batch (default: 10)
- `enable_file_monitoring`: Monitor file access (true/false)
- `enable_network_monitoring`: Monitor network connections (true/false)
- `enable_process_monitoring`: Monitor processes (true/false)

## Events Collected

### Login Events
- Login time
- Location (based on network)
- IP address

### File Access Events
- File path
- Action (read/write/delete)
- Timestamp

### Network Events
- Remote IP address
- Port number
- Connection status

### Process Events
- Privilege escalation attempts
- Admin/sudo processes

## Network Isolation

When an anomaly is detected, the backend can send an isolation command:

**Windows**: Disables all network adapters using PowerShell
**Linux**: Disables eth0/wlan0 interfaces

**Requirements**: Administrator/sudo privileges

## Troubleshooting

### Agent won't start
- Check backend URL is correct
- Ensure backend is running
- Verify network connectivity

### Events not appearing in dashboard
- Check backend logs for errors
- Verify employee_id in config.json
- Test backend API: `curl http://YOUR_IP:8000/api/employees`

### Network isolation not working
- Run agent as Administrator
- Check Windows Firewall settings
- Verify PowerShell execution policy

## Security Notes

⚠️ **Important**: This agent requires elevated privileges for network isolation. Only install on machines you have permission to monitor.

For hackathon demos:
- Use on your own devices or with explicit consent
- Explain the monitoring to participants
- Have a clear opt-out mechanism

## Demo Tips

1. **Show real-time monitoring**: Open dashboard while agent runs
2. **Trigger anomalies**: Access unusual files, connect to unusual ports
3. **Demonstrate isolation**: Click "Isolate" button and show network disconnection
4. **Restore connectivity**: Toggle back to show network restoration

## Support

For issues or questions, check the main SentinelAI README or backend logs.
