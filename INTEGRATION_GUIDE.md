# node³ Integration Guide 🚀

## Overview

The node³ system is now fully integrated! The frontend marketplace UI connects to the backend production marketplace, and local GPU agents can accept and execute jobs automatically.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  http://localhost:8080 (Agent Dashboard)                    │
│  http://localhost:8080/marketplace (Browse Jobs/Providers)  │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴──────────────┐
         │                          │
         ▼                          ▼
┌──────────────────┐      ┌──────────────────┐
│   Agent (8080)   │◄────►│ Marketplace      │
│  - Dashboard     │      │ (8000)           │
│  - GPU Monitor   │      │ - Job Queue      │
│  - Job Executor  │      │ - Payments       │
│  - Local GPU     │      │ - Agent Registry │
└──────────────────┘      └──────────────────┘
         │                          │
         │                          │
         ▼                          ▼
┌──────────────────┐      ┌──────────────────┐
│  Solana Wallet   │      │  PostgreSQL DB   │
│  (Devnet)        │      │  (or SQLite)     │
└──────────────────┘      └──────────────────┘
```

## Components

### 1. Production Marketplace (`production_marketplace.py`)
- FastAPI server running on port 8000
- PostgreSQL/SQLite database for persistence
- Solana payment processing
- Agent registration and authentication
- Job queue management

### 2. GPU Agent (`main.py`)
- Detects local GPU hardware
- Registers with marketplace
- Polls for available jobs
- Executes jobs on local GPU
- Reports results and receives payments

### 3. Dashboard (`dashboard.py`)
- Web UI on port 8080
- Real-time GPU monitoring
- Job history and earnings
- Marketplace browser integration

### 4. Marketplace UI (`templates/marketplace.html`)
- Browse available jobs
- View compute providers
- Dark/light theme
- Real-time updates
- GPU-only marketplace

## Quick Start

### Option 1: Integrated Startup (Recommended)

Start everything at once:

```bash
python start_integrated_system.py
```

This will:
1. Start the production marketplace
2. Detect your GPU
3. Register your agent
4. Start the agent dashboard
5. Begin accepting jobs automatically

### Option 2: Manual Startup

Start components separately for more control:

```bash
# Terminal 1: Start marketplace
python production_marketplace.py

# Terminal 2: Start agent (after marketplace is running)
python main.py
```

## Testing the Integration

### Automated End-to-End Test

```bash
# Start the system first
python start_integrated_system.py

# In another terminal, run the test
python test_end_to_end.py
```

This tests the complete flow:
1. ✅ Marketplace health check
2. ✅ Agent online and registered
3. ✅ Job creation
4. ✅ Job acceptance by agent
5. ✅ Job execution on GPU
6. ✅ Payment processing
7. ✅ Stats updated

### Manual Testing

#### 1. Create a Test Job

```bash
python marketplace_admin.py create-job \
  --job-type test \
  --reward 0.001 \
  --requires-gpu
```

#### 2. Watch Agent Accept It

Open http://localhost:8080 and watch:
- Job appears in marketplace
- Agent automatically accepts it
- Job executes on your GPU
- Payment is processed
- Balance updates

#### 3. View Statistics

```bash
python marketplace_admin.py stats
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Marketplace
MARKETPLACE_URL=http://localhost:8000
DATABASE_URL=sqlite+aiosqlite:///./marketplace.db
MARKETPLACE_PORT=8000

# Agent
AGENT_PORT=8080
API_KEY=<your_api_key>  # Auto-generated on registration
WALLET_PATH=./wallet.json
SOLANA_RPC_URL=https://api.devnet.solana.com

# Optional
SKIP_GPU_CHECK=false  # Set to true for demo mode without GPU
```

### Wallet Setup

The system needs two wallets:

1. **Agent Wallet** (`wallet.json`)
   - Receives payments for completed jobs
   - Created automatically on first run

2. **Marketplace Wallet** (`marketplace_wallet.json`)
   - Pays agents for completed jobs
   - Created automatically or copy from agent wallet

## API Endpoints

### Marketplace APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/agents/register` | POST | Register new agent |
| `/api/jobs/available` | POST | Get available jobs |
| `/api/jobs/{id}/accept` | POST | Accept a job |
| `/api/jobs/{id}/complete` | POST | Report completion |
| `/api/jobs/{id}/fail` | POST | Report failure |
| `/api/marketplace/agents` | GET | List all agents |
| `/api/admin/jobs/create` | POST | Create new job (admin) |
| `/api/admin/stats` | GET | Get statistics (admin) |

### Agent/Dashboard APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Agent dashboard |
| `/marketplace` | GET | Marketplace browser |
| `/api/status` | GET | Agent status |
| `/api/jobs` | GET | Job history |
| `/api/earnings` | GET | Earnings stats |
| `/api/marketplace/jobs` | GET | Available marketplace jobs |
| `/api/marketplace/agents` | GET | All registered agents |

## How Job Execution Works

### 1. Job Posting
- Someone posts a job to the marketplace via API or admin CLI
- Job includes: type, reward, GPU requirements, Docker image, command

### 2. Job Discovery
- Agent polls marketplace every 10 seconds
- Marketplace returns jobs matching agent's GPU capabilities
- Agent automatically evaluates if it can handle the job

### 3. Job Acceptance
- Agent accepts job via API
- Provides wallet address for payment
- Job status changes to "accepted"

### 4. Job Execution
- Agent downloads input data (if provided)
- Executes job using:
  - **Native execution** (default, works out-of-box)
  - **Docker container** (optional, for isolation)
- Monitors for timeout
- Captures output

### 5. Result Submission
- Agent uploads results (if URL provided)
- Reports completion to marketplace
- Includes execution time and metrics

### 6. Payment
- Marketplace automatically processes payment
- Sends SOL to agent's wallet
- Updates agent's earnings stats
- Records transaction signature

## Monitoring

### Real-Time Dashboard

Open http://localhost:8080 to see:
- **GPU Utilization**: Real-time metrics
- **Active Jobs**: Currently executing
- **Job History**: Past 50 jobs
- **Earnings**: Total and today
- **Wallet Balance**: Current SOL balance

### Marketplace Browser

Open http://localhost:8080/marketplace to see:
- **Available Jobs**: All jobs in marketplace
- **Compute Providers**: All registered agents
- **Filters**: Sort by reward, GPU memory, framework
- **Stats**: Total jobs, agents, average reward

### Logs

```bash
# Agent logs
tail -f logs/node3_agent_$(date +%Y-%m-%d).log

# Marketplace logs
# (displayed in terminal where marketplace is running)
```

## Troubleshooting

### Agent Won't Register

**Problem**: Agent fails to register with marketplace

**Solutions**:
```bash
# 1. Check marketplace is running
curl http://localhost:8000/health

# 2. Check wallet exists
ls wallet.json

# 3. Check logs for errors
tail -f logs/node3_agent_*.log

# 4. Try manual registration
python -c "
import requests
import json

with open('wallet.json') as f:
    wallet = json.load(f)

response = requests.post('http://localhost:8000/api/agents/register', json={
    'wallet_address': 'YOUR_WALLET_ADDRESS',
    'gpu_model': 'Demo GPU',
    'gpu_vendor': 'Demo',
    'gpu_memory': 8000000000
})
print(response.json())
"
```

### Jobs Not Being Accepted

**Problem**: Jobs remain in "available" status

**Solutions**:
```bash
# 1. Check agent is running
curl http://localhost:8080/api/status

# 2. Verify API key is set
grep API_KEY .env

# 3. Check agent can reach marketplace
curl http://localhost:8000/api/marketplace/agents

# 4. Check job requirements match GPU
python marketplace_admin.py stats
```

### Payment Not Processing

**Problem**: Job completes but payment doesn't arrive

**Solutions**:
```bash
# 1. Check marketplace wallet has funds
python marketplace_admin.py wallet-info

# 2. Fund marketplace wallet (devnet)
python marketplace_admin.py fund-wallet

# 3. Check payment history
python marketplace_admin.py payment-history

# 4. Verify wallet address is correct
grep wallet_address wallet.json
```

### GPU Not Detected

**Problem**: System can't find your GPU

**Solutions**:
```bash
# 1. Test GPU detection
python -c "
from gpu_detector import GPUDetector
detector = GPUDetector()
gpus = detector.detect_gpus()
print(f'Found {len(gpus)} GPUs')
for gpu in gpus:
    print(f'  - {gpu.name}')
"

# 2. Run in demo mode (for testing without GPU)
echo "SKIP_GPU_CHECK=true" >> .env
python main.py

# 3. Check drivers
# NVIDIA: nvidia-smi
# AMD: rocm-smi
# Apple: system_profiler SPDisplaysDataType
```

## Production Deployment

### Requirements

- PostgreSQL database (not SQLite)
- Production Solana RPC endpoint
- Domain name with SSL/TLS
- Sufficient SOL in marketplace wallet

### Steps

1. **Setup Database**
```bash
# Create PostgreSQL database
createdb node3_marketplace

# Set database URL
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/node3_marketplace"
```

2. **Configure Marketplace**
```bash
# Set production environment
export ENVIRONMENT=production
export SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Generate admin API key
export ADMIN_API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Fund marketplace wallet
solana transfer MARKETPLACE_WALLET_ADDRESS 10 --url mainnet-beta
```

3. **Deploy with PM2** (or similar)
```bash
pm2 start production_marketplace.py --name marketplace
pm2 start main.py --name agent
pm2 save
```

4. **Setup Nginx Reverse Proxy**
```nginx
server {
    listen 80;
    server_name marketplace.your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Next Steps

✅ **System is Integrated!**

You can now:

1. **Test Locally**: Run end-to-end tests
2. **Create Jobs**: Use marketplace admin CLI
3. **Monitor Performance**: Watch dashboard
4. **Scale Up**: Add more agents
5. **Go Live**: Deploy to production

## Support

- 📧 Check logs for detailed errors
- 🐛 Run test suite: `python test_end_to_end.py`
- 📊 View stats: `python marketplace_admin.py stats`
- 🔧 Health check: `curl http://localhost:8000/health`

---

**Your node³ distributed GPU compute network is ready!** 🎉

