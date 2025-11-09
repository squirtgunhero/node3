# Download and Test Instructions

## For You (Developer)

### Quick Local Test

```bash
# 1. Navigate to project
cd /Users/michaelehrlich/Desktop/node3agent

# 2. Create .env for demo mode
echo "SKIP_GPU_CHECK=true" > .env
echo "DASHBOARD_PORT=8080" >> .env

# 3. Run executable
./dist/node3-agent
```

Then open: http://127.0.0.1:8080

## For End Users (Download)

### Step 1: Download

1. Get the executable from:
   - GitHub Releases (when uploaded)
   - Direct download link
   - Or copy `dist/node3-agent` to share

### Step 2: Prepare

```bash
# Make executable (if needed)
chmod +x node3-agent

# Create .env file for configuration
cat > .env << 'EOF'
SKIP_GPU_CHECK=true
DASHBOARD_PORT=8080
SOLANA_RPC_URL=https://api.devnet.solana.com
EOF
```

### Step 3: Run

```bash
# Run the executable
./node3-agent
```

### Step 4: Access Dashboard

Open browser to: **http://127.0.0.1:8080**

### If macOS Blocks It

```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine node3-agent

# Or allow in System Preferences → Security & Privacy
```

## Testing Checklist

- [ ] Executable runs without errors
- [ ] Dashboard loads at http://127.0.0.1:8080
- [ ] Wallet address is displayed
- [ ] GPU info shows (or demo mode message)
- [ ] No Python installation required
- [ ] All dependencies included

## Creating Download Package

```bash
# Create release package
mkdir -p release-package
cp dist/node3-agent release-package/
cp README.md release-package/
cp .env.example release-package/

# Create quick start
cat > release-package/QUICKSTART.txt << 'EOF'
node3 Agent - Quick Start

1. Run: ./node3-agent
2. Open browser: http://127.0.0.1:8080
3. Configure in .env file if needed

For demo mode, create .env with:
SKIP_GPU_CHECK=true
EOF

# Create ZIP
zip -r node3-agent-release.zip release-package/
```

