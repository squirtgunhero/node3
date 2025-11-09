# Quick Start Guide

## Start the Dashboard

### Option 1: Run Python Script (Development)

```bash
cd /Users/michaelehrlich/Desktop/node3agent
python main.py
```

Dashboard will be available at: **http://127.0.0.1:8080**

### Option 2: Run Executable (Production)

```bash
cd /Users/michaelehrlich/Desktop/node3agent
./dist/node3-agent
```

Dashboard will be available at: **http://127.0.0.1:8080**

## Access the Dashboard

1. Open your web browser
2. Navigate to: **http://127.0.0.1:8080**
3. You should see the node3 Agent dashboard

## If Dashboard Doesn't Load

### Check if server is running:
```bash
# Check if process is running
ps aux | grep "python main.py" | grep -v grep

# Check if port 8080 is in use
lsof -i :8080
```

### Check logs:
```bash
tail -f logs/node3_agent_*.log
```

### Common Issues:

1. **Port already in use:**
   ```bash
   # Kill existing process
   pkill -f "python main.py"
   # Or change port in .env: DASHBOARD_PORT=8081
   ```

2. **Firewall blocking:**
   - Check macOS Firewall settings
   - Ensure localhost connections are allowed

3. **Server crashed:**
   - Check logs in `logs/` directory
   - Restart the server

## Stopping the Server

Press `Ctrl+C` in the terminal, or:
```bash
pkill -f "python main.py"
```

## Testing the API

```bash
# Check status
curl http://127.0.0.1:8080/api/status

# Check earnings
curl http://127.0.0.1:8080/api/earnings

# Check jobs
curl http://127.0.0.1:8080/api/jobs
```

