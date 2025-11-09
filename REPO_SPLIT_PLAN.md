# Repository Split Plan

## Current Situation
- Single repo `node3agent` contains both marketplace and agent code
- Need to split into two separate repos for better architecture

## Target Structure

### Repo 1: `node3-marketplace`
**Purpose**: Centralized marketplace server
**Deployment**: Cloud server (single instance or scaled)
**Users**: Job posters, marketplace operators

**Contents**:
- `production_marketplace.py` - Main marketplace API
- `load_balancer.py` - Load balancing system
- `marketplace_admin.py` - Admin CLI tools
- `payment_module.py` - Payment processing
- `templates/marketplace.html` - Public marketplace UI
- `test_marketplace_integration.py` - Marketplace tests
- `LOAD_BALANCING.md` - Load balancer docs
- `INTEGRATION_GUIDE.md` - Marketplace integration guide
- `requirements_marketplace.txt` - Server dependencies
- Docker/deployment configs

### Repo 2: `node3-agent`
**Purpose**: GPU agent software
**Deployment**: User's local machine (thousands of instances)
**Users**: GPU providers, compute sellers

**Contents**:
- `main.py` - Agent entry point
- `job_manager.py` - Job execution manager
- `gpu_detector.py` - GPU detection
- `docker_manager.py` - Container management
- `native_executor.py` - Native execution
- `dashboard.py` - Agent dashboard
- `payment_module.py` - Payment receiving
- `templates/index.html` - Agent dashboard UI
- `build.py` - Build executables
- `test_dashboard_ui.py` - Dashboard test server
- `test_end_to_end.py` - E2E tests
- GPU/build documentation
- `requirements.txt` - Agent dependencies

## Shared Code

These files are needed by both:
- `payment_module.py` - Payment operations
- API models/schemas (could extract to SDK later)

**Decision**: Duplicate for now, extract to SDK later if needed

## Migration Steps

### Step 1: Backup & Commit Current State
```bash
cd ~/Desktop/node3agent
git add .
git commit -m "Pre-split snapshot: Complete integrated system with load balancing"
git push origin main
```

### Step 2: Create Marketplace Repo
```bash
cd ~/Desktop
cp -r node3agent node3-marketplace
cd node3-marketplace

# Remove agent-specific files
rm -f main.py build.py gpu_detector.py docker_manager.py native_executor.py
rm -f build_*.py release.py setup.py
rm -f test_agent_connection.py test_dashboard_ui.py test_end_to_end.py
rm -rf build/ dist/ lima/
rm -f templates/index.html

# Keep only marketplace files
# Initialize as new repo
rm -rf .git
git init
git add .
git commit -m "Initial commit: node3 Marketplace"
```

### Step 3: Clean Agent Repo
```bash
cd ~/Desktop/node3agent

# Remove marketplace-specific files
git rm production_marketplace.py load_balancer.py marketplace_admin.py
git rm templates/marketplace.html
git rm test_marketplace_integration.py test_marketplace_ui.py
git rm LOAD_BALANCING.md LOAD_BALANCING_SUMMARY.md
git rm MARKETPLACE_DEPLOYMENT.md PRODUCTION_MARKETPLACE.md

# Update README to focus on agent
git commit -m "Split repos: Removed marketplace code, focused on agent"
```

### Step 4: Update Configuration

**Marketplace `.env.example`**:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/node3_marketplace
SOLANA_RPC_URL=https://api.devnet.solana.com
MARKETPLACE_WALLET_PATH=./marketplace_wallet.json
ADMIN_API_KEY=your-admin-key-here
PORT=8000
ENVIRONMENT=development
```

**Agent `.env.example`**:
```env
MARKETPLACE_URL=https://api.node3.com
API_KEY=your-agent-api-key
WALLET_PATH=./wallet.json
SOLANA_RPC_URL=https://api.devnet.solana.com
DASHBOARD_PORT=8080
SKIP_GPU_CHECK=false
```

### Step 5: Update Documentation

Each repo gets its own:
- README.md (specific to that component)
- QUICKSTART.md
- API documentation (if applicable)
- Deployment guide

### Step 6: Create GitHub Repos

```bash
# On GitHub, create:
# 1. node3-marketplace (public or private)
# 2. node3-agent (likely public)

# Push marketplace
cd ~/Desktop/node3-marketplace
git remote add origin https://github.com/YOUR_USERNAME/node3-marketplace.git
git push -u origin main

# Push updated agent
cd ~/Desktop/node3agent
git remote set-url origin https://github.com/YOUR_USERNAME/node3-agent.git
git push origin main
```

## File Mapping

### Files Moving to Marketplace
```
✓ production_marketplace.py
✓ load_balancer.py
✓ marketplace_admin.py
✓ templates/marketplace.html
✓ test_marketplace_integration.py
✓ test_marketplace_ui.py
✓ LOAD_BALANCING.md
✓ LOAD_BALANCING_SUMMARY.md
✓ MARKETPLACE_DEPLOYMENT.md
✓ PRODUCTION_MARKETPLACE.md
✓ mock_marketplace.py (for testing)
✓ requirements_marketplace.txt
✓ Dockerfile.marketplace
✓ docker-compose.marketplace.yml
```

### Files Staying in Agent
```
✓ main.py
✓ job_manager.py
✓ gpu_detector.py
✓ docker_manager.py
✓ native_executor.py
✓ dashboard.py
✓ templates/index.html
✓ build.py, build_*.py, release.py
✓ test_agent_connection.py
✓ test_dashboard_ui.py
✓ test_end_to_end.py
✓ GPU_*.md docs
✓ BUILD*.md docs
✓ requirements.txt
✓ Dockerfile (for agent)
```

### Files in Both (Duplicated)
```
✓ payment_module.py
✓ .gitignore
✓ LICENSE
```

## Testing After Split

### Test Marketplace
```bash
cd ~/Desktop/node3-marketplace
python -m venv venv
source venv/bin/activate
pip install -r requirements_marketplace.txt
python production_marketplace.py
```

### Test Agent
```bash
cd ~/Desktop/node3agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Test Integration
```bash
# Terminal 1: Start marketplace
cd ~/Desktop/node3-marketplace
python production_marketplace.py

# Terminal 2: Start agent (point to localhost marketplace)
cd ~/Desktop/node3agent
export MARKETPLACE_URL=http://localhost:8000
python main.py
```

## Benefits After Split

1. **Clear Separation**: Marketplace and agent have distinct purposes
2. **Independent Deployment**: Update one without touching the other
3. **Better Security**: Marketplace code isolated from agent execution
4. **Easier Collaboration**: Different teams can work independently
5. **Cleaner Codebase**: Each repo is focused and maintainable

## Next Steps After Split

1. Update documentation in each repo
2. Create separate CI/CD pipelines
3. Consider extracting shared code to `node3-sdk` package
4. Set up separate issue trackers
5. Create release workflows for each

## Rollback Plan

If something goes wrong:
```bash
cd ~/Desktop/node3agent
git log  # Find the pre-split commit
git reset --hard <commit-hash>
```

The pre-split snapshot is safely committed!

