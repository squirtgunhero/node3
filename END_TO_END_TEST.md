# End-to-End Test Guide

## Prerequisites
- Mock marketplace running (already started)
- Agent code ready

## Step 1: Start Mock Marketplace
```bash
python mock_marketplace.py
```
Marketplace runs on: http://127.0.0.1:8000

## Step 2: Test Marketplace Connection
```bash
python test_marketplace_connection.py
```

## Step 3: Start Agent with Mock Marketplace

### Option A: Set environment variable inline
```bash
MARKETPLACE_URL=http://127.0.0.1:8000 python main.py
```

### Option B: Create/update .env file
Create a `.env` file with:
```
MARKETPLACE_URL=http://127.0.0.1:8000
API_KEY=test-key
SKIP_GPU_CHECK=false
```

Then run:
```bash
python main.py
```

## Step 4: Verify Agent Connection

1. Check agent logs for:
   - "Polling marketplace for jobs..."
   - "Job available: {job_id}"
   - "Accepted job: {job_id}"

2. Check dashboard at: http://127.0.0.1:8080
   - Should show GPU info
   - Should show active jobs
   - Should show wallet balance

3. Check marketplace status:
   ```bash
   curl http://127.0.0.1:8000/api/status
   ```
   Should show registered agents and jobs

## Expected Flow

1. Agent starts → Detects GPU → Connects to marketplace
2. Marketplace returns available jobs
3. Agent accepts job (if Docker available)
4. Agent executes job in Docker container
5. Agent reports completion to marketplace
6. Payment processed (mock)

## Troubleshooting

**Issue: Agent can't connect to marketplace**
- Verify marketplace is running: `curl http://127.0.0.1:8000/`
- Check MARKETPLACE_URL is set correctly

**Issue: No jobs returned**
- Check GPU memory requirement (needs >= 2GB)
- Check marketplace logs for errors

**Issue: Jobs not executing**
- Docker may not be available (expected on macOS)
- Agent will still connect and show jobs in dashboard
- See GPU_STATUS.md for details

## Success Indicators

✅ Marketplace running and accessible
✅ Agent connects to marketplace
✅ Jobs are returned with unique IDs
✅ Dashboard shows agent status
✅ Agent accepts jobs (if Docker available)

