# Production Marketplace Deployment Guide

Complete guide to deploying your node3 production marketplace.

## 🏗️ Architecture

```
┌─────────────────┐
│   Agents        │
│   (worldwide)   │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────┐
│  Load Balancer  │
│  (Nginx/AWS)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐      ┌──────────────┐
│  Marketplace    │←────→│  PostgreSQL  │
│  FastAPI Server │      │   Database   │
└────────┬────────┘      └──────────────┘
         │
         ↓
┌─────────────────┐
│  Solana Network │
│  (Payments)     │
└─────────────────┘
```

---

## 📋 Prerequisites

### Required:
- ✅ Linux server (Ubuntu 20.04+ recommended)
- ✅ Docker & Docker Compose
- ✅ 2GB+ RAM
- ✅ 20GB+ disk space
- ✅ PostgreSQL 15+
- ✅ Domain name (for HTTPS)

### Optional:
- Redis (for caching)
- Monitoring (Grafana, Prometheus)
- CDN (Cloudflare)

---

## 🚀 Quick Start (Docker Compose)

### 1. Clone Repository

```bash
git clone https://github.com/your-repo/node3agent.git
cd node3agent
```

### 2. Configure Environment

```bash
# Copy example config
cp marketplace_config.example.env .env

# Generate admin API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env with your values
nano .env
```

### 3. Create Marketplace Wallet

```bash
# Create Solana wallet for marketplace
python3 -c "
from solders.keypair import Keypair
import json

keypair = Keypair()
wallet_data = {
    'public_key': str(keypair.pubkey()),
    'private_key': list(bytes(keypair))
}

with open('marketplace_wallet.json', 'w') as f:
    json.dump(wallet_data, f, indent=2)

print(f'Wallet created: {keypair.pubkey()}')
"

# Fund wallet (devnet)
# Visit: https://faucet.solana.com
# Enter your wallet address and request SOL
```

### 4. Start Services

```bash
# Start all services
docker-compose -f docker-compose.marketplace.yml up -d

# Check status
docker-compose -f docker-compose.marketplace.yml ps

# View logs
docker-compose -f docker-compose.marketplace.yml logs -f marketplace
```

### 5. Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# Expected: {"status":"healthy",...}
```

---

## 🔧 Manual Installation (Without Docker)

### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Redis (optional)
sudo apt install redis-server -y
```

### 2. Setup Database

```bash
# Create database
sudo -u postgres createdb node3_marketplace

# Create user
sudo -u postgres psql -c "CREATE USER node3 WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE node3_marketplace TO node3;"
```

### 3. Setup Application

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
pip install -r requirements_marketplace.txt

# Create .env file
cp marketplace_config.example.env .env
nano .env  # Edit configuration
```

### 4. Create Wallet & Fund

```bash
# Create marketplace wallet (see Docker step 3)

# Fund wallet on devnet/mainnet
```

### 5. Run Marketplace

```bash
# Development
python production_marketplace.py

# Production (with gunicorn)
pip install gunicorn
gunicorn production_marketplace:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 6. Setup Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/node3-marketplace.service
```

```ini
[Unit]
Description=node3 Marketplace API
After=network.target postgresql.service

[Service]
Type=simple
User=node3
WorkingDirectory=/home/node3/node3agent
Environment="PATH=/home/node3/node3agent/venv/bin"
ExecStart=/home/node3/node3agent/venv/bin/python production_marketplace.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable node3-marketplace
sudo systemctl start node3-marketplace

# Check status
sudo systemctl status node3-marketplace
```

---

## 🌐 Production Setup

### 1. Domain & HTTPS

#### Using Nginx

```bash
# Install Nginx
sudo apt install nginx certbot python3-certbot-nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/marketplace
```

```nginx
server {
    listen 80;
    server_name api.node3.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/marketplace /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d api.node3.com
```

#### Using Caddy (Simpler)

```bash
# Install Caddy
sudo apt install caddy -y

# Create Caddyfile
sudo nano /etc/caddy/Caddyfile
```

```
api.node3.com {
    reverse_proxy localhost:8000
}
```

```bash
sudo systemctl reload caddy
```

---

## 🔐 Security Checklist

### Before Going Live:

- [ ] **Change all default passwords**
  - PostgreSQL password
  - Admin API key
  - PGAdmin password

- [ ] **Enable HTTPS**
  - SSL certificate installed
  - Force HTTPS redirect

- [ ] **Secure API keys**
  - Store in environment variables
  - Never commit to git
  - Rotate regularly

- [ ] **Configure CORS**
  - Set specific origins (not `*`)
  - Update in production_marketplace.py

- [ ] **Setup firewall**
  ```bash
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw allow 22/tcp
  sudo ufw enable
  ```

- [ ] **Backup database**
  ```bash
  # Create backup script
  pg_dump node3_marketplace > backup_$(date +%Y%m%d).sql
  ```

- [ ] **Monitor logs**
  - Setup log rotation
  - Configure alerting

- [ ] **Use mainnet Solana**
  - Change RPC URL
  - Fund marketplace wallet with real SOL

---

## 📊 Admin Tasks

### Create Test Jobs

```bash
# Using curl
curl -X POST http://localhost:8000/api/admin/jobs/create \
  -H "X-API-Key: YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "inference",
    "docker_image": "python:3.11-slim",
    "command": ["python", "-c", "print(\"Hello\")"],
    "environment": {},
    "gpu_memory_required": 0,
    "requires_gpu": false,
    "estimated_duration": 30,
    "timeout": 60,
    "reward": 0.001
  }'
```

### View Statistics

```bash
curl http://localhost:8000/api/admin/stats \
  -H "X-API-Key: YOUR_ADMIN_API_KEY"
```

### Check Marketplace Wallet

```bash
curl http://localhost:8000/api/marketplace/info \
  -H "X-API-Key: YOUR_ADMIN_API_KEY"
```

---

## 🧪 Testing

### Test Agent Registration

```bash
curl -X POST http://localhost:8000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "YOUR_AGENT_WALLET",
    "gpu_model": "RTX 3090",
    "gpu_vendor": "NVIDIA",
    "gpu_memory": 24000000000,
    "compute_capability": {"major": 8, "minor": 6}
  }'

# Save the API key returned!
```

### Test Job Flow

```bash
# 1. Register agent (see above)
# 2. Get available jobs
curl -X POST http://localhost:8000/api/jobs/available \
  -H "X-API-Key: AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "gpu_model": "RTX 3090",
    "gpu_memory": 24000000000,
    "max_concurrent_jobs": 1
  }'

# 3. Accept job
curl -X POST http://localhost:8000/api/jobs/JOB_ID/accept \
  -H "X-API-Key: AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "YOUR_WALLET"}'

# 4. Complete job
curl -X POST http://localhost:8000/api/jobs/JOB_ID/complete \
  -H "X-API-Key: AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "output_data": {"result": "success"},
    "execution_time": 25.5
  }'
```

---

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  marketplace:
    deploy:
      replicas: 3
  
  nginx:
    image: nginx:alpine
    depends_on:
      - marketplace
    # Load balancer config
```

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_agent ON jobs(agent_id);
CREATE INDEX idx_agents_api_key ON agents(api_key);

-- Vacuum regularly
VACUUM ANALYZE;
```

---

## 🔍 Monitoring

### Health Checks

```bash
# Add to cron
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart node3-marketplace
```

### Prometheus Metrics

Add to `production_marketplace.py`:
```python
from prometheus_client import Counter, Histogram, Gauge

jobs_completed = Counter('jobs_completed_total', 'Total jobs completed')
payment_amount = Counter('payment_amount_sol', 'Total SOL paid')
active_agents = Gauge('active_agents', 'Number of active agents')
```

---

## 🆘 Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -U postgres -d node3_marketplace -c "SELECT 1;"

# View logs
sudo journalctl -u postgresql -n 50
```

### Payment Failures

```bash
# Check marketplace wallet balance
curl http://localhost:8000/api/marketplace/info \
  -H "X-API-Key: YOUR_ADMIN_API_KEY"

# Fund wallet if low
```

### High CPU Usage

```bash
# Check processes
top
htop

# Check database queries
sudo -u postgres psql node3_marketplace
\x
SELECT * FROM pg_stat_activity;
```

---

## 📚 Next Steps

After deployment:

1. ✅ **Test everything** - Run through entire job flow
2. ✅ **Monitor logs** - Watch for errors
3. ✅ **Update agent** - Point to production marketplace
4. ✅ **Create jobs** - Add real jobs to marketplace
5. ✅ **Invite beta agents** - Start with small group
6. ✅ **Scale gradually** - Monitor and adjust

---

## 🔗 Useful Links

- Database migrations: [Alembic](https://alembic.sqlalchemy.org/)
- Monitoring: [Grafana](https://grafana.com/)
- Load testing: [Locust](https://locust.io/)
- Solana docs: [Solana Docs](https://docs.solana.com/)

---

## 💡 Production Checklist

Before going live:

- [ ] HTTPS enabled
- [ ] Firewall configured
- [ ] Database backed up
- [ ] Monitoring setup
- [ ] Logs rotating
- [ ] Secrets secured
- [ ] CORS configured
- [ ] Rate limiting enabled
- [ ] Health checks active
- [ ] Mainnet wallet funded
- [ ] Domain DNS configured
- [ ] SSL certificate valid
- [ ] Load tested
- [ ] Documentation updated
- [ ] Team trained

**Ready to launch!** 🚀

