# How to Test the node3 Agent

Complete guide for testing the agent with the mock marketplace and test jobs.

## Prerequisites

Before testing, make sure you have:
- ✅ Python 3.10+ installed
- ✅ Docker installed and running (optional, but needed for job execution)
- ✅ All dependencies installed: `pip install -r requirements.txt`

## Quick Test Guide

### Option 1: Quick Test (Without Docker)

This tests the marketplace connection and job flow without executing jobs:

```bash
# Terminal 1: Start Mock Marketplace
python mock_marketplace.py

# Terminal 2: Start Agent (no Docker needed)
MARKETPLACE_URL=http://127.0.0.1:8000 SKIP_GPU_CHECK=true python main.py
```

**What to check:**
- Agent connects to marketplace
- Dashboard shows at http://127.0.0.1:8080
- Jobs appear in dashboard (but won't execute without Docker)

### Option 2: Full Test (With Docker)

This tests the complete flow including job execution:

```bash
# Step 1: Build test Docker images
cd test_jobs
./build_test_images.sh

# Step 2: Start Mock Marketplace (Terminal 1)
cd ..
python mock_marketplace.py

# Step 3: Start Agent (Terminal 2)
MARKETPLACE_URL=http://127.0.0.1:8000 python main.py
```

**What to check:**
- Agent connects to marketplace
- Jobs are retrieved and accepted
- Jobs execute in Docker containers
- Results are uploaded
- Jobs marked as completed

## Step-by-Step Testing

### Step 1: Verify Test Images are Built

```bash
# Check if images exist
docker images | grep node3-test

# If not, build them
cd test_jobs
./build_test_images.sh
```

Expected output:
```
✓ Simple test image built
✓ Math test image built
✓ File processing test image built
```

### Step 2: Start Mock Marketplace

```bash
python mock_marketplace.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Loaded 4 test job template(s) from test_jobs.json
```

**Verify marketplace is running:**
```bash
curl http://127.0.0.1:8000/
```

Should return:
```json
{
  "message": "Mock node3 Marketplace API",
  "status": "running"
}
```

### Step 3: Test Marketplace Connection

In a new terminal:
```bash
python test_job_execution.py
```

This runs automated tests:
- ✅ Marketplace connection
- ✅ Job retrieval
- ✅ Job acceptance
- ✅ Job completion reporting
- ✅ Docker execution (if available)

### Step 4: Start the Agent

**Option A: Using environment variables**
```bash
MARKETPLACE_URL=http://127.0.0.1:8000 python main.py
```

**Option B: Using .env file**
Create `.env` file:
```bash
MARKETPLACE_URL=http://127.0.0.1:8000
API_KEY=test-key
SKIP_GPU_CHECK=false
DASHBOARD_PORT=8080
```

Then run:
```bash
python main.py
```

### Step 5: Monitor the Agent

**Watch the logs** for:
```
INFO: Job manager started
INFO: Polling marketplace for jobs...
INFO: Retrieved 4 job(s) from marketplace
INFO: Accepted job: <job_id>
INFO: Executing job <job_id>
INFO: Job <job_id> completed successfully
```

**Check the dashboard** at http://127.0.0.1:8080:
- GPU information displayed
- Wallet address shown
- Active jobs count
- Job history

**Check marketplace status:**
```bash
curl http://127.0.0.1:8000/api/status
```

Should show:
```json
{
  "status": "running",
  "available_jobs": 4,
  "accepted_jobs": <number>,
  "registered_agents": 1
}
```

## Testing Scenarios

### Scenario 1: Test Job Acceptance Flow

1. Start marketplace: `python mock_marketplace.py`
2. Start agent: `MARKETPLACE_URL=http://127.0.0.1:8000 python main.py`
3. Watch logs for:
   - "Polling marketplace for jobs..."
   - "Retrieved X job(s)"
   - "Accepted job: <id>"

**Expected:** Agent connects, retrieves jobs, accepts them

### Scenario 2: Test Job Execution (Requires Docker)

1. Build images: `cd test_jobs && ./build_test_images.sh`
2. Start marketplace: `python mock_marketplace.py`
3. Start agent: `MARKETPLACE_URL=http://127.0.0.1:8000 python main.py`
4. Watch logs for:
   - "Executing job <id>"
   - "Container completed successfully"
   - "Job <id> completed successfully"

**Expected:** Jobs execute in Docker and complete

### Scenario 3: Test Without Docker

1. Start marketplace: `python mock_marketplace.py`
2. Start agent: `MARKETPLACE_URL=http://127.0.0.1:8000 SKIP_GPU_CHECK=true python main.py`
3. Watch logs for:
   - "Docker not available"
   - "Job manager polling enabled (job execution disabled)"
   - Jobs appear but don't execute

**Expected:** Agent connects and shows jobs, but jobs don't execute

### Scenario 4: Test Dashboard

1. Start agent: `python main.py`
2. Open browser: http://127.0.0.1:8080
3. Check:
   - GPU information displayed
   - Wallet address shown
   - Job status updates
   - Real-time metrics

**Expected:** Dashboard loads and shows current status

## Automated Testing

### Run All Tests

```bash
# Test marketplace connection and job flow
python test_job_execution.py

# Test agent connection (if you have test_agent_connection.py)
python test_agent_connection.py

# Test marketplace connection
python test_marketplace_connection.py
```

### Run Unit Tests

```bash
# Test GPU detector
pytest tests/test_gpu_detector.py

# Test Docker manager
pytest tests/test_docker_manager.py
```

## What to Look For

### ✅ Success Indicators

**Marketplace:**
- Server starts on port 8000
- Loads test jobs from JSON
- Returns jobs to agent requests
- Tracks accepted/completed jobs

**Agent:**
- Connects to marketplace successfully
- Retrieves jobs from marketplace
- Accepts jobs automatically
- Executes jobs (if Docker available)
- Reports completion to marketplace
- Dashboard accessible and updating

**Dashboard:**
- Loads at http://127.0.0.1:8080
- Shows GPU information
- Shows wallet address and balance
- Shows active/completed jobs
- Updates in real-time

### ❌ Common Issues

**Marketplace won't start:**
- Check port 8000 is not in use: `lsof -i :8000`
- Check test_jobs.json exists and is valid JSON
- Check dependencies: `pip install fastapi uvicorn`

**Agent won't connect:**
- Verify marketplace is running: `curl http://127.0.0.1:8000/`
- Check MARKETPLACE_URL is correct
- Check network connectivity

**Jobs won't execute:**
- Verify Docker is running: `docker ps`
- Check test images are built: `docker images | grep node3-test`
- Check Docker logs for errors
- Verify Docker has permissions

**Dashboard won't load:**
- Check port 8080 is not in use: `lsof -i :8080`
- Check firewall settings
- Check agent logs for errors

## Debugging Tips

### Check Marketplace Logs
Look for:
- Job templates loaded
- Agent registration
- Job requests received
- Job acceptances

### Check Agent Logs
Look for:
- GPU detection
- Docker initialization
- Marketplace connection
- Job polling
- Job execution

### Check Docker
```bash
# List running containers
docker ps

# Check container logs
docker logs <container_id>

# List test images
docker images | grep node3-test
```

### Check Network
```bash
# Test marketplace endpoint
curl http://127.0.0.1:8000/api/status

# Test agent dashboard
curl http://127.0.0.1:8080/api/status
```

## Test Checklist

- [ ] Test images built successfully
- [ ] Marketplace starts and loads jobs
- [ ] Agent connects to marketplace
- [ ] Agent retrieves jobs
- [ ] Agent accepts jobs
- [ ] Jobs execute (if Docker available)
- [ ] Jobs complete successfully
- [ ] Results reported to marketplace
- [ ] Dashboard displays correctly
- [ ] Real-time updates work

## Next Steps After Testing

Once testing is successful:

1. **Integration Tests** - Create comprehensive integration tests
2. **Performance Testing** - Test with multiple concurrent jobs
3. **Error Handling** - Test failure scenarios
4. **Production Testing** - Test with real marketplace (when available)

## Need Help?

- Check `TEST_JOB_SYSTEM.md` for test job details
- Check `TEST_RESULTS.md` for previous test results
- Check `NEXT_STEPS.md` for what to build next
- Check logs in `logs/` directory

