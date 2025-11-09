# Test Marketplace Setup Guide

## Quick Start

### 1. Start Mock Marketplace

```bash
# Terminal 1: Start marketplace
cd /Users/michaelehrlich/Desktop/node3agent
python mock_marketplace.py
```

Marketplace will run at: **http://127.0.0.1:8000**

### 2. Configure Agent

Update `.env` file:
```bash
MARKETPLACE_URL=http://127.0.0.1:8000
API_KEY=test_key_123
SKIP_GPU_CHECK=true
DASHBOARD_PORT=8080
SOLANA_RPC_URL=https://api.devnet.solana.com
```

### 3. Start Agent

```bash
# Terminal 2: Start agent
python main.py
```

Agent dashboard: **http://127.0.0.1:8080**

## What Happens

1. Agent connects to mock marketplace
2. Marketplace returns test jobs
3. Agent accepts jobs
4. Jobs execute (if Docker works)
5. Results reported back

## Test Endpoints

```bash
# Check marketplace status
curl http://127.0.0.1:8000/api/status

# List jobs
curl http://127.0.0.1:8000/api/jobs

# Check agent status
curl http://127.0.0.1:8080/api/status
```

## Next Steps

Once mock marketplace works:
1. Fix Docker integration
2. Create real test jobs
3. Test full workflow
4. Deploy real marketplace

