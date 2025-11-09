#!/bin/bash
# Script to split node3agent into marketplace and agent repos

set -e  # Exit on error

echo "🔄 Starting repository split..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Create marketplace repo
echo -e "${YELLOW}Step 1: Creating node3-marketplace repo${NC}"
cd ~/Desktop
rm -rf node3-marketplace 2>/dev/null || true
cp -r node3agent node3-marketplace
cd node3-marketplace

echo "  Removing agent-specific files..."
# Remove agent-specific files
rm -f main.py
rm -f gpu_detector.py
rm -f docker_manager.py
rm -f native_executor.py
rm -f build.py build_linux.py build_windows.py release.py setup.py setup_codesign.sh
rm -f test_agent_connection.py
rm -f test_gpu_detector.py
rm -f test_docker_manager.py
rm -f test_job_execution.py
rm -f test_executable.sh
rm -f node3-agent.spec node3-agent-installer.dmg
rm -f create_dmg.sh
rm -rf build/ dist/ lima/
rm -rf __pycache__/

# Remove agent-specific docs
rm -f BUILD.md BUILD_CROSS_PLATFORM.md MACOS_BUILD_FIX.md
rm -f RELEASE_BUILD.md RELEASE_CHECKLIST.md RELEASE_GUIDE.md
rm -f CODE_SIGNING.md WINDOWS_ICON_FIX.md UTF8_ENCODING_FIX.md
rm -f BUNDLE_LIMA.md LIMA_BUNDLING_COMPLETE.md LIMA_INTEGRATION.md
rm -f DOCKER_ALTERNATIVES.md NATIVE_EXECUTION.md
rm -f GPU_MONITORING_TRUTH.md GPU_STATUS.md
rm -f USER_EXPERIENCE.md WHAT_NEXT.md NEXT_STEPS.md

# Remove agent dashboard
rm -f templates/index.html
rm -f dashboard.py

# Remove agent tests
rm -f test_dashboard_ui.py
rm -f test_end_to_end.py
rm -f tests/test_docker_manager.py
rm -f tests/test_gpu_detector.py
rm -rf test_jobs/

# Remove build artifacts
rm -rf venv/

# Remove split plan (no longer needed)
rm -f REPO_SPLIT_PLAN.md

# Keep marketplace files
echo "  Keeping marketplace files..."
# production_marketplace.py
# load_balancer.py
# marketplace_admin.py
# payment_module.py
# templates/marketplace.html
# test_marketplace_integration.py
# test_marketplace_ui.py
# LOAD_BALANCING*.md
# MARKETPLACE_*.md

# Create marketplace-specific README
cat > README.md << 'EOF'
# node³ Marketplace

Centralized marketplace server for the node³ distributed GPU compute network.

## Features

- 🔄 **Load Balancing** - Intelligent job distribution across agents
- 💰 **Payment Processing** - Automatic SOL payments via Solana
- 🔍 **Job Queue** - Priority-based job queuing system
- 💪 **Fault Tolerance** - Automatic retry and failover
- 📊 **Real-time Monitoring** - Agent health tracking
- 🎯 **Smart Assignment** - Agent scoring algorithm

## Quick Start

```bash
# Install dependencies
pip install -r requirements_marketplace.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start marketplace
python production_marketplace.py
```

## Documentation

- [Integration Guide](INTEGRATION_GUIDE.md)
- [Load Balancing](LOAD_BALANCING.md)
- [API Documentation](API.md)
- [Deployment](DEPLOYMENT.md)

## Architecture

The marketplace serves as the central coordin

ator for the node³ network:
- Manages job queue with priority
- Tracks agent capacity and health
- Processes payments automatically
- Provides public API for job posting

## Requirements

- Python 3.11+
- PostgreSQL (or SQLite for development)
- Solana wallet with devnet/mainnet SOL

## API Endpoints

- `POST /api/agents/register` - Register new agent
- `POST /api/jobs/available` - Get available jobs
- `POST /api/jobs/{id}/accept` - Accept a job
- `POST /api/jobs/{id}/complete` - Report completion
- `GET /api/marketplace/agents` - List all agents
- `POST /api/admin/jobs/create` - Create new job (admin)

See [API.md](API.md) for full documentation.

## License

MIT
EOF

# Create .env.example
cat > .env.example << 'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/node3_marketplace
# Or for development: DATABASE_URL=sqlite+aiosqlite:///./marketplace.db

# Solana
SOLANA_RPC_URL=https://api.devnet.solana.com
MARKETPLACE_WALLET_PATH=./marketplace_wallet.json

# Server
PORT=8000
ENVIRONMENT=development

# Admin
ADMIN_API_KEY=your-secure-admin-key-here
EOF

# Rename requirements
if [ -f requirements_marketplace.txt ]; then
    mv requirements_marketplace.txt requirements.txt
else
    # Create marketplace-specific requirements
    cat > requirements.txt << 'EOF'
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
loguru>=0.7.2
python-dotenv>=1.0.0
sqlalchemy>=2.0.23
asyncpg>=0.29.0
aiosqlite>=0.19.0
solders>=0.18.0
solana>=0.30.0
pydantic>=2.5.0
EOF
fi

# Initialize as new git repo
rm -rf .git
git init
git add .
git commit -m "Initial commit: node³ Marketplace

Centralized marketplace server for distributed GPU compute network.

Features:
- Load balancing with intelligent job distribution
- Automatic payment processing (Solana)
- Agent health monitoring and failover
- Priority-based job queue
- Real-time statistics

Split from main node3agent repo for cleaner architecture."

echo -e "${GREEN}✓ Marketplace repo created at ~/Desktop/node3-marketplace${NC}"
echo ""

# Step 2: Clean agent repo
echo -e "${YELLOW}Step 2: Cleaning agent repo${NC}"
cd ~/Desktop/node3agent

echo "  Removing marketplace-specific files..."
git rm -f production_marketplace.py load_balancer.py marketplace_admin.py mock_marketplace.py 2>/dev/null || true
git rm -f templates/marketplace.html 2>/dev/null || true
git rm -f test_marketplace_integration.py test_marketplace_ui.py 2>/dev/null || true
git rm -f LOAD_BALANCING.md LOAD_BALANCING_SUMMARY.md 2>/dev/null || true
git rm -f MARKETPLACE_DEPLOYMENT.md MARKETPLACE_SUMMARY.md PRODUCTION_MARKETPLACE.md 2>/dev/null || true
git rm -f requirements_marketplace.txt 2>/dev/null || true
git rm -f Dockerfile.marketplace docker-compose.marketplace.yml 2>/dev/null || true
git rm -f INTEGRATION_COMPLETE.md INTEGRATION_GUIDE.md QUICKSTART_INTEGRATED.md 2>/dev/null || true
git rm -f MARKETPLACE_TESTING.md 2>/dev/null || true
git rm -f start_integrated_system.py 2>/dev/null || true
git rm -f REPO_SPLIT_PLAN.md split_repos.sh 2>/dev/null || true

# Update agent README
cat > README.md << 'EOF'
# node³ Agent

GPU agent software for the node³ distributed compute network. Run this on your machine to earn SOL by providing GPU compute power.

## Features

- 🎮 **GPU Detection** - Supports NVIDIA, AMD, Apple Silicon, Intel
- 🐳 **Flexible Execution** - Docker or native execution
- 💰 **Automatic Earnings** - Get paid in SOL automatically
- 📊 **Dashboard** - Monitor your GPU and earnings
- 🔄 **Auto-Updates** - Stay current with latest features
- 🛡️ **Secure** - Jobs run in isolated environments

## Quick Start

```bash
# Download and run
./node3-agent

# Or from source
python main.py
```

Visit http://localhost:8080 to see your dashboard.

## Installation

### Option 1: Pre-built Binary (Easiest)

Download from releases and run:
```bash
chmod +x node3-agent
./node3-agent
```

### Option 2: From Source

```bash
git clone https://github.com/YOUR_USERNAME/node3-agent.git
cd node3-agent
pip install -r requirements.txt
python main.py
```

## Requirements

- Python 3.11+ (if running from source)
- GPU with drivers installed
- Docker (optional, for containerized jobs)

### GPU Support

- **NVIDIA**: CUDA toolkit
- **AMD**: ROCm drivers
- **Apple Silicon**: Built-in Metal support
- **Intel**: OpenCL drivers

See [GPU_SUPPORT.md](GPU_MONITORING_TRUTH.md) for details.

## Configuration

Create a `.env` file:

```env
MARKETPLACE_URL=https://api.node3.com
WALLET_PATH=./wallet.json
DASHBOARD_PORT=8080
```

## Documentation

- [Quick Start](QUICKSTART.md)
- [Building](BUILD.md)
- [Testing](TESTING.md)
- [Troubleshooting](HOW_TO_TEST.md)

## How It Works

1. Agent detects your GPU
2. Registers with marketplace
3. Polls for available jobs
4. Executes jobs on your GPU
5. Reports results
6. Receives SOL payment automatically

## Dashboard

Access at http://localhost:8080:
- GPU utilization
- Active jobs
- Earnings history
- System status

## Building

```bash
# Build for your platform
python build.py

# Cross-platform
python build_linux.py
python build_windows.py
```

See [BUILD.md](BUILD.md) for details.

## License

MIT
EOF

# Commit changes
git add -A
git commit -m "Split repos: Remove marketplace code, focus on agent

Removed:
- Marketplace server (production_marketplace.py)
- Load balancer (load_balancer.py)
- Marketplace admin tools
- Marketplace UI
- Marketplace-specific documentation

The agent now connects to a separate marketplace server.

Updated README to focus on agent functionality and user experience."

echo -e "${GREEN}✓ Agent repo cleaned${NC}"
echo ""

# Step 3: Summary
echo "================================================"
echo -e "${GREEN}✅ Repository split complete!${NC}"
echo "================================================"
echo ""
echo "📦 Two repos created:"
echo ""
echo "1️⃣  node3-marketplace (~/Desktop/node3-marketplace)"
echo "   - Centralized marketplace server"
echo "   - Load balancing system"
echo "   - Payment processing"
echo "   - Admin tools"
echo ""
echo "2️⃣  node3-agent (~/Desktop/node3agent)"
echo "   - GPU agent software"
echo "   - Job execution"
echo "   - Dashboard"
echo "   - Build tools"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Test marketplace:"
echo "   cd ~/Desktop/node3-marketplace"
echo "   python -m venv venv && source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   python production_marketplace.py"
echo ""
echo "2. Test agent:"
echo "   cd ~/Desktop/node3agent"
echo "   python main.py"
echo ""
echo "3. Create GitHub repos and push:"
echo "   # For marketplace"
echo "   cd ~/Desktop/node3-marketplace"
echo "   git remote add origin https://github.com/YOUR_USERNAME/node3-marketplace.git"
echo "   git push -u origin main"
echo ""
echo "   # For agent (update remote)"
echo "   cd ~/Desktop/node3agent"
echo "   # Rename repo on GitHub to node3-agent first, then:"
echo "   git push origin main"
echo ""
echo "🎉 Split complete!"

