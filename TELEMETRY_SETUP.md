
# Real-Time Agent Monitoring Setup

Complete guide to set up real-time monitoring of all Node3 agents with status, GPU info, and location tracking.

## 🎯 What You Get

- **Real-time dashboard** matching Node3 branding
- **Live agent tracking** - see all installed agents
- **Detailed metrics**:
  - MAC address
  - Hostname
  - Platform (Windows/Linux/macOS)
  - GPU type and memory
  - Current status (online/offline/working)
  - Location (city, country)
  - Total jobs completed
  - Total SOL earned
  - Last seen time

## 📋 Architecture

```
┌──────────────┐          ┌──────────────────┐          ┌─────────────────┐
│ Agent (User) │  ────>   │ Telemetry Server │  <────   │ Admin Dashboard │
│   Installs   │   HTTP   │   (FastAPI +     │  WebSocket│  (Real-time)   │
│              │          │    SQLite DB)    │          │                 │
└──────────────┘          └──────────────────┘          └─────────────────┘
```

1. **Agent** sends telemetry data on startup and every 60 seconds
2. **Server** stores data in SQLite database
3. **Dashboard** shows real-time updates via WebSocket

## 🚀 Quick Start

### Step 1: Start Telemetry Server

```bash
cd ~/Desktop/node3agent

# Install dependencies
pip3 install --break-system-packages fastapi uvicorn websockets

# Start server
python3 telemetry_server.py
```

**Server will run at:** http://localhost:8888

### Step 2: Open Dashboard

Open your browser to:
```
http://localhost:8888
```

**Marketplace View (Default):** Beautiful card-based grid layout
**Table View:** http://localhost:8888/table - Classic table layout

You'll see:
- Total agents registered
- Online agents count  
- Jobs completed
- SOL earned
- Real-time cards/table of all agents with:
  - Status badges with animations
  - GPU information
  - Location data
  - MAC addresses
  - Earnings tracking

### Step 3: Integrate Into Agent

Add telemetry to your `main.py`:

```python
from agent_telemetry import AgentTelemetry

# After GPU detection
telemetry = AgentTelemetry(telemetry_url="https://your-server.com")
telemetry.register(gpu_info, agent_version=VERSION)

# In main loop (every 60 seconds)
telemetry.send_heartbeat(
    status='working' if active_jobs else 'idle',
    total_jobs=completed_jobs_count,
    total_earnings=total_earned_sol
)

# After job completion
telemetry.log_event('job_completed', {
    'job_id': job_id,
    'duration': duration_seconds,
    'reward': reward_amount
})
```

## 🌐 Deploy to Production

### Option 1: DigitalOcean / AWS / GCP

**1. Create a server (Ubuntu 22.04)**

```bash
# SSH into server
ssh root@your-server-ip

# Install Python and dependencies
apt update
apt install python3 python3-pip -y
pip3 install fastapi uvicorn websockets

# Copy files
scp telemetry_server.py root@your-server-ip:/opt/node3/
scp admin_dashboard.html root@your-server-ip:/opt/node3/

# Create systemd service
cat > /etc/systemd/system/node3-telemetry.service <<EOF
[Unit]
Description=Node3 Telemetry Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/node3
ExecStart=/usr/bin/python3 telemetry_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl daemon-reload
systemctl enable node3-telemetry
systemctl start node3-telemetry
```

**2. Configure Nginx (reverse proxy)**

```bash
apt install nginx -y

cat > /etc/nginx/sites-available/node3-telemetry <<EOF
server {
    listen 80;
    server_name telemetry.node3.com;

    location / {
        proxy_pass http://localhost:8888;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/node3-telemetry /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

**3. Add SSL (Let's Encrypt)**

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d telemetry.node3.com
```

**4. Update agent telemetry URL:**

```python
telemetry = AgentTelemetry(telemetry_url="https://telemetry.node3.com")
```

### Option 2: Railway / Render / Fly.io (Easier)

**1. Create `requirements.txt`:**

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
```

**2. Create `Procfile`:**

```
web: python3 telemetry_server.py
```

**3. Deploy:**

- Railway: Connect GitHub repo, auto-deploys
- Render: Create Web Service, connect repo
- Fly.io: `fly launch` then `fly deploy`

**4. Get your URL and update agent:**

```python
telemetry = AgentTelemetry(telemetry_url="https://your-app.railway.app")
```

## 🔒 Security & Privacy

### What's Collected

- ✅ **Anonymous agent ID** (UUID, not personally identifiable)
- ✅ **MAC address** (for unique identification)
- ✅ **Hostname** (computer name)
- ✅ **Platform info** (Windows/Linux/macOS)
- ✅ **GPU info** (vendor, model, memory)
- ✅ **Approximate location** (city, country from IP)
- ✅ **Usage stats** (jobs completed, earnings)

### What's NOT Collected

- ❌ IP addresses (only used to get location, not stored)
- ❌ Personal information
- ❌ Job contents or data
- ❌ Wallet private keys
- ❌ File system information
- ❌ Browsing history

### Privacy Controls

**1. Make it opt-in** (add to your installer):

```python
# Ask user during installation
enable_telemetry = input("Enable anonymous telemetry? (y/n): ").lower() == 'y'

# Save preference
config = {'telemetry_enabled': enable_telemetry}
```

**2. Add opt-out mechanism:**

```python
# In agent settings
if not config.get('telemetry_enabled', True):
    telemetry.telemetry_enabled = False
```

**3. Show in privacy policy:**

```
Node3 Agent collects anonymous usage statistics including:
- GPU model and performance
- Jobs completed and earnings
- Approximate location (city/country)
This helps us improve the service. You can opt-out anytime.
```

## 📊 Dashboard Features

### Real-Time Stats

- **Total Agents**: All registered agents
- **Online Now**: Currently active
- **Total Jobs**: Completed across all agents
- **Total Earned**: SOL paid out

### Agent Table

Columns:
- Status (online/offline/working)
- Hostname
- Platform (with icon)
- GPU vendor and model
- GPU memory
- Location (city, country)
- MAC address
- Jobs completed
- Earnings (SOL)
- Last seen time

### Filters

- All agents
- Online only
- Offline only

### Live Updates

- Auto-refreshes via WebSocket
- See agents come online/offline in real-time
- Watch job completions as they happen

## 🎨 Customization

### Change Branding

Edit `admin_dashboard.html`:

```css
/* Change colors */
:root {
    --accent: #007AFF;  /* Your brand color */
    --success: #30D158;
    --warning: #FF9F0A;
}
```

### Add More Metrics

1. **Update database** (`telemetry_server.py`):

```python
c.execute('''ALTER TABLE agents ADD COLUMN cpu_cores INTEGER''')
```

2. **Send from agent** (`agent_telemetry.py`):

```python
data['cpu_cores'] = os.cpu_count()
```

3. **Display in dashboard** (`admin_dashboard.html`):

```html
<td>${agent.cpu_cores} cores</td>
```

## 📈 Analytics Queries

### Most Popular GPU

```bash
sqlite3 telemetry.db "SELECT gpu_model, COUNT(*) as count FROM agents GROUP BY gpu_model ORDER BY count DESC LIMIT 10"
```

### Platform Distribution

```bash
sqlite3 telemetry.db "SELECT platform, COUNT(*) as count FROM agents GROUP BY platform"
```

### Top Earners

```bash
sqlite3 telemetry.db "SELECT hostname, total_earnings FROM agents ORDER BY total_earnings DESC LIMIT 10"
```

### Geographic Distribution

```bash
sqlite3 telemetry.db "SELECT country, COUNT(*) as count FROM agents GROUP BY country ORDER BY count DESC"
```

## 🔧 Troubleshooting

### Agents Not Showing Up

1. **Check server is running:**
   ```bash
   curl http://localhost:8888/api/stats
   ```

2. **Check agent can reach server:**
   ```python
   # Add to agent
   logger.info(f"Telemetry URL: {telemetry.telemetry_url}")
   ```

3. **Check firewall:**
   ```bash
   # On server
   ufw allow 8888/tcp
   ```

### WebSocket Not Connecting

1. **Check browser console** for errors
2. **Verify WebSocket URL** matches server
3. **Check for SSL issues** (wss:// for HTTPS sites)

### Database Corruption

```bash
# Backup
cp telemetry.db telemetry.db.backup

# Rebuild
python3 telemetry_server.py  # Will recreate tables
```

## 📱 Mobile App (Future)

The telemetry API is designed to support mobile apps:

```swift
// iOS Swift
struct TelemetryAPI {
    let baseURL = "https://telemetry.node3.com"
    
    func sendHeartbeat() async {
        // ...
    }
}
```

```kotlin
// Android Kotlin
class TelemetryService {
    val baseUrl = "https://telemetry.node3.com"
    
    suspend fun sendHeartbeat() {
        // ...
    }
}
```

## 🎯 Next Steps

1. **Start the server** locally for testing
2. **Integrate telemetry** into your agent
3. **Deploy to production** server
4. **Monitor your fleet** in real-time!

---

**Support:** If you need help, check the logs:
```bash
# Server logs
journalctl -u node3-telemetry -f

# Agent logs
tail -f ~/.node3-agent/agent.log
```

Enjoy real-time monitoring of your Node3 agent network! 📊🚀

