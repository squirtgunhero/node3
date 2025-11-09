# Quick Test Guide

## Fastest Way to Test (5 minutes)

### 1. Start Marketplace (Terminal 1)
```bash
python mock_marketplace.py
```
✅ Should see: "Loaded 4 test job template(s)"

### 2. Test Connection (Terminal 2)
```bash
python test_marketplace_connection.py
```
✅ Should see: "✅ All tests passed!"

### 3. Start Agent (Terminal 2, after test)
```bash
MARKETPLACE_URL=http://127.0.0.1:8000 python main.py
```
✅ Should see: "Job manager started" and "Dashboard available at..."

### 4. Open Dashboard
Open browser: http://127.0.0.1:8080
✅ Should see: GPU info, wallet, jobs

## Test Job Execution (Requires Docker)

### Build Test Images First
```bash
cd test_jobs
./build_test_images.sh
```

### Then Run Full Test
```bash
python test_job_execution.py
```

## What You Should See

**Marketplace Logs:**
```
INFO: Loaded 4 test job template(s)
INFO: Agent requesting jobs: ...
INFO: Returning 4 job(s) to agent
```

**Agent Logs:**
```
INFO: Job manager started
INFO: Polling marketplace for jobs...
INFO: Retrieved 4 job(s) from marketplace
INFO: Accepted job: <job_id>
```

**Dashboard:**
- GPU information
- Wallet address
- Active jobs count
- Job history table

## Troubleshooting

**Marketplace won't start?**
- Check port 8000: `lsof -i :8000`
- Check test_jobs.json exists

**Agent won't connect?**
- Verify marketplace running: `curl http://127.0.0.1:8000/`
- Check MARKETPLACE_URL

**Jobs won't execute?**
- Build images: `cd test_jobs && ./build_test_images.sh`
- Check Docker: `docker ps`

For detailed guide, see `HOW_TO_TEST.md`

