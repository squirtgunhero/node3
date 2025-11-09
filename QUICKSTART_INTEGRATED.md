# node³ Quick Start - Integrated System 🚀

Get your GPU earning SOL in 5 minutes!

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Create wallet (if you don't have one)
python -c "from payment_module import PaymentModule; import asyncio; asyncio.run(PaymentModule.create_wallet('./wallet.json'))"
```

## Start the System

### One Command Start

```bash
python start_integrated_system.py
```

That's it! This will:
- ✅ Start the marketplace server
- ✅ Detect your GPU
- ✅ Register your agent
- ✅ Start the dashboard
- ✅ Begin accepting jobs

### What You'll See

```
============================================================
  node³ Integrated System Startup
============================================================

[10:30:45] INFO     | Checking prerequisites...
[10:30:45] INFO     | Starting production marketplace on port 8000...
[10:30:48] INFO     | ✓ Marketplace is ready!
[10:30:48] INFO     | Detecting local GPU...
[10:30:48] INFO     | ✓ GPU detected: NVIDIA GeForce RTX 4090
[10:30:48] INFO     |   Vendor: NVIDIA
[10:30:48] INFO     |   Memory: 24.0 GB
[10:30:48] INFO     |   Framework: cuda
[10:30:49] INFO     | Registering GPU agent with marketplace...
[10:30:49] INFO     | ✓ Agent registered successfully!
[10:30:49] INFO     |   Agent ID: agent_1234
[10:30:49] INFO     |   GPU: NVIDIA GeForce RTX 4090
[10:30:49] INFO     |   Wallet: 9xQeWvG8...LDvK6Rh4
[10:30:49] INFO     | ✓ API key saved to .env
[10:30:50] INFO     | Starting GPU agent on port 8080...
[10:30:52] INFO     | ✓ Agent Dashboard is ready!

============================================================
  ✅ node³ System is Running!
============================================================

🏪 Marketplace API:     http://localhost:8000
🤖 Agent Dashboard:     http://localhost:8080
🏪 Marketplace Browser: http://localhost:8080/marketplace

📋 Next Steps:
  1. Open agent dashboard to monitor your GPU
  2. Post a test job to the marketplace:
     python marketplace_admin.py create-job --reward 0.001
  3. Watch your agent automatically accept and execute the job
  4. Receive SOL payment upon completion

Press Ctrl+C to stop the system
```

## Open Your Dashboard

Navigate to:
- **Agent Dashboard**: http://localhost:8080
- **Marketplace**: http://localhost:8080/marketplace

## Post Your First Job

In a new terminal:

```bash
# Simple test job
python marketplace_admin.py create-job \
  --job-type test \
  --reward 0.001

# GPU inference job
python marketplace_admin.py create-job \
  --job-type inference \
  --reward 0.005 \
  --requires-gpu \
  --gpu-memory 8000000000
```

## Watch the Magic Happen

1. **Job Posted** → Marketplace receives job
2. **Agent Detects** → Your agent polls and sees the job
3. **Auto Accept** → Agent accepts if GPU matches requirements
4. **Execute** → Job runs on your GPU
5. **Complete** → Results submitted
6. **Payment** → SOL arrives in your wallet! 💰

## View Your Earnings

```bash
# Quick stats
curl http://localhost:8080/api/earnings | python -m json.tool

# Detailed stats
python marketplace_admin.py stats
```

## Test End-to-End

Run the automated test suite:

```bash
python test_end_to_end.py
```

Expected output:
```
============================================================
  node³ End-to-End Integration Test
============================================================

Phase 1: System Health
✓ Marketplace is healthy
✓ Agent is online
✓ Agent registered in marketplace

Phase 2: Job Creation
✓ Created test job in marketplace

Phase 3: Job Execution
⏳ Waiting for agent to accept job (max 30s)...
✓ Agent accepts job
⏳ Waiting for job execution (max 60s)...
✓ Job executes successfully

Phase 4: Payment & Stats
⏳ Waiting for payment (max 10s)...
✓ Payment processed
✓ Marketplace stats updated

============================================================
Results: 8/8 tests passed (100.0%)
✅ All end-to-end tests passed!
============================================================
```

## Common Commands

```bash
# Create multiple test jobs
python marketplace_admin.py create-test-jobs --count 10 --reward 0.0001

# View marketplace statistics
python marketplace_admin.py stats

# Check marketplace health
curl http://localhost:8000/health

# Check agent status
curl http://localhost:8080/api/status

# View payment history
python marketplace_admin.py payment-history

# Fund marketplace wallet (devnet only)
python marketplace_admin.py fund-wallet
```

## Monitor in Real-Time

Open these URLs while system is running:

1. **Agent Dashboard**
   - http://localhost:8080
   - See GPU utilization, active jobs, earnings

2. **Marketplace Browser**
   - http://localhost:8080/marketplace
   - Browse jobs and compute providers
   - Real-time updates

3. **API Status**
   - http://localhost:8000/health (Marketplace)
   - http://localhost:8080/api/status (Agent)

## Troubleshooting

### "No GPU detected"

Run in demo mode:
```bash
export SKIP_GPU_CHECK=true
python start_integrated_system.py
```

### "Marketplace failed to start"

Check if port 8000 is available:
```bash
lsof -i :8000
# Kill any process using port 8000
kill -9 <PID>
```

### "Agent won't register"

Manually register:
```bash
python -c "
import requests
import json

with open('wallet.json') as f:
    wallet_data = json.load(f)
    from solders.keypair import Keypair
    kp = Keypair.from_base58_string(wallet_data['private_key'])
    wallet = str(kp.pubkey())

response = requests.post('http://localhost:8000/api/agents/register', json={
    'wallet_address': wallet,
    'gpu_model': 'My GPU',
    'gpu_vendor': 'NVIDIA',
    'gpu_memory': 8000000000
})
print(response.json())
"
```

## Stop the System

Press `Ctrl+C` in the terminal running `start_integrated_system.py`

Both marketplace and agent will shut down gracefully.

## What's Next?

✅ System is running
✅ Agent is registered
✅ Ready to earn SOL

Now you can:
- Post real jobs
- Scale to multiple agents
- Deploy to production
- Integrate with your applications

## Need Help?

- Read: `INTEGRATION_GUIDE.md` for detailed documentation
- Check logs: `logs/node3_agent_*.log`
- Test: `python test_end_to_end.py`
- Stats: `python marketplace_admin.py stats`

---

**You're now running a decentralized GPU compute network!** 🎉🚀

