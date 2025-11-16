# 🚀 Node3 Agent Monitoring - Quick Start

Real-time monitoring dashboard matching your marketplace design.

## ⚡ 2-Minute Setup

```bash
cd ~/Desktop/node3agent

# Install dependencies (one-time)
pip3 install --break-system-packages fastapi uvicorn websockets

# Start server
./start_telemetry.sh
```

**Dashboard:** http://localhost:8888  
**Alternative Table View:** http://localhost:8888/table

That's it! 🎉

---

## 📸 What You Get

### Marketplace View (Default)
- **Beautiful card-based layout** matching your marketplace design
- **Purple/blue gradient accents**
- **Animated status badges** (pulse for working agents)
- **Visual agent cards** showing:
  - Status (Online 🟢 / Working ⚡ / Offline ⚫)
  - Platform icon (Windows 🪟 / Linux 🐧 / macOS 🍎)
  - GPU vendor and memory
  - Location (city, country)
  - MAC address
  - Jobs completed
  - SOL earned
  - Last seen time
- **Search & filter** functionality
- **Real-time updates** via WebSocket

### Table View (Alternative)
- **Classic table layout** for detailed monitoring
- **Apple-style design** with glass morphism
- **Compact view** - see more agents at once
- **Dark/light theme toggle**

---

## 🎯 Agent Integration

Add to your `main.py`:

```python
from agent_telemetry import AgentTelemetry

# Initialize (one-time)
telemetry = AgentTelemetry(telemetry_url="http://localhost:8888")

# Register on startup
telemetry.register(gpu_info, agent_version="1.0.0")

# Send heartbeat every 60 seconds
telemetry.send_heartbeat(
    status='working' if has_active_jobs else 'idle',
    total_jobs=completed_jobs_count,
    total_earnings=total_sol_earned
)

# Log events
telemetry.log_event('job_completed', {
    'job_id': job_id,
    'reward': reward_sol
})
```

---

## 🌐 Deploy to Production

### Option 1: Railway (Easiest)

1. Create `requirements.txt`:
   ```
   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   websockets==12.0
   ```

2. Push to GitHub

3. Connect to Railway - auto-deploys!

4. Update agents:
   ```python
   telemetry = AgentTelemetry(telemetry_url="https://your-app.railway.app")
   ```

### Option 2: Your Server

```bash
# On Ubuntu server
apt install python3 python3-pip nginx -y
pip3 install fastapi uvicorn websockets

# Setup systemd service
# See TELEMETRY_SETUP.md for details

# Add SSL with Let's Encrypt
certbot --nginx -d telemetry.yournode3.com
```

---

## 📊 Features

### Stats Overview
- Total agents registered
- Online agents now
- Total jobs completed
- Total SOL earned

### Filters
- All Agents
- 🟢 Online only
- ⚡ Working only
- ⚫ Offline only

### Search
- By hostname
- By GPU model
- By GPU vendor

### Real-Time
- WebSocket updates
- Live status changes
- Instant job tracking

---

## 🎨 Customization

### Change Colors

Edit `marketplace_monitor.html`:

```css
:root {
    --accent-purple: #764ba2;  /* Your purple */
    --accent-blue: #667eea;    /* Your blue */
}
```

### Add Your Logo

```html
<div class="header-left">
    <img src="your-logo.png" alt="Logo" style="height: 40px; margin-bottom: 12px;">
    <h1>Your Brand Marketplace</h1>
</div>
```

---

## 🔍 What's Tracked

### Automatically Collected
- ✅ **Agent ID** (unique UUID)
- ✅ **MAC address** (for identification)
- ✅ **Hostname** (computer name)
- ✅ **Platform** (Windows/Linux/macOS)
- ✅ **GPU info** (vendor, model, memory)
- ✅ **Location** (city, country from IP)
- ✅ **Status** (online/working/offline)
- ✅ **Jobs** (completed count)
- ✅ **Earnings** (SOL earned)
- ✅ **Last seen** (timestamp)

### Privacy-Friendly
- ❌ No IP addresses stored
- ❌ No personal information
- ❌ No job contents
- ❌ No wallet keys
- ✅ Anonymous telemetry
- ✅ Can be opt-out

---

## 📱 Mobile Friendly

The marketplace view is fully responsive:
- Works on phones
- Works on tablets
- Works on desktop
- Touch-friendly
- Swipe to scroll

---

## 🔄 Auto-Refresh

- **WebSocket**: Instant updates when agents change
- **Fallback**: Polls every 30 seconds if WebSocket fails
- **Reconnection**: Automatically reconnects if disconnected

---

## 🧪 Test It

```bash
# Start server
./start_telemetry.sh

# In another terminal, send test data
./test_telemetry.sh

# Open browser
open http://localhost:8888
```

You'll see a test agent appear in the dashboard!

---

## 📖 Learn More

- **Full Setup Guide:** `TELEMETRY_SETUP.md`
- **Dashboard Comparison:** `DASHBOARD_VIEWS.md`
- **Code Documentation:** `agent_telemetry.py`

---

## 💡 Tips

1. **Bookmark both views** - Marketplace for demos, table for ops
2. **Use search** - Find agents quickly
3. **Watch animations** - Working agents pulse
4. **Check locations** - See global distribution
5. **Monitor real-time** - Status updates instantly

---

## 🆘 Troubleshooting

### Server won't start
```bash
# Check if port 8888 is in use
lsof -i :8888

# Kill existing process
pkill -f telemetry_server
```

### Agents not appearing
1. Check server is running: `curl http://localhost:8888/api/stats`
2. Check agent telemetry URL is correct
3. Check firewall allows port 8888

### WebSocket not connecting
1. Check browser console for errors
2. Verify WebSocket URL in dashboard
3. Check for SSL issues (use wss:// for HTTPS)

---

## ✅ Quick Checklist

- [ ] Server running: `./start_telemetry.sh`
- [ ] Dashboard accessible: http://localhost:8888
- [ ] WebSocket shows "Live" status
- [ ] Agent telemetry integrated
- [ ] Test agent appears in dashboard
- [ ] Real-time updates working

---

**Your marketplace-styled monitoring is ready!** 🎨📊

Start the server and watch your agent network come to life! 🚀

