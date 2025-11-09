# Testing Guide

## Quick Test (Local)

### 1. Test the Built Executable

```bash
# Navigate to project directory
cd /Users/michaelehrlich/Desktop/node3agent

# Run the executable
./dist/node3-agent

# Or use the .app bundle
open dist/node3-agent.app
```

### 2. Test in Demo Mode

Since you don't have an NVIDIA GPU, test with demo mode:

```bash
# Create .env file for demo mode
echo "SKIP_GPU_CHECK=true" > .env
echo "DASHBOARD_PORT=8080" >> .env
echo "SOLANA_RPC_URL=https://api.devnet.solana.com" >> .env

# Run executable
./dist/node3-agent
```

Then open browser to: http://127.0.0.1:8080

## Testing Checklist

### Basic Functionality
- [ ] Executable runs without errors
- [ ] Dashboard loads at http://127.0.0.1:8080
- [ ] GPU detection works (or demo mode works)
- [ ] Wallet creation/loading works
- [ ] Dashboard shows wallet address
- [ ] Dashboard shows GPU information
- [ ] WebSocket connection works (real-time updates)

### Clean System Test

To test on a clean system:

1. **Copy executable to a new location:**
```bash
# Create test directory
mkdir ~/node3-test
cp dist/node3-agent ~/node3-test/
cd ~/node3-test
```

2. **Create minimal .env file:**
```bash
cat > .env << EOF
SKIP_GPU_CHECK=true
DASHBOARD_PORT=8080
SOLANA_RPC_URL=https://api.devnet.solana.com
EOF
```

3. **Run from clean location:**
```bash
./node3-agent
```

4. **Verify:**
   - Executable runs without Python installed
   - Dashboard accessible
   - No import errors

## Distribution Testing

### For macOS Users

1. **Download the executable**
2. **Open Terminal and navigate to download location**
3. **Make executable:**
```bash
chmod +x node3-agent
```

4. **Run:**
```bash
./node3-agent
```

5. **If macOS blocks it:**
   - Go to System Preferences → Security & Privacy
   - Click "Open Anyway" next to the blocked message
   - Or: `xattr -d com.apple.quarantine node3-agent`

### Test Checklist for Downloaders

- [ ] Downloaded executable runs
- [ ] No Python installation required
- [ ] Dashboard accessible
- [ ] GPU detection works (if GPU available)
- [ ] Wallet creation works
- [ ] No missing dependencies errors

## Troubleshooting

### "Permission denied"
```bash
chmod +x node3-agent
```

### "Cannot be opened because it is from an unidentified developer"
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine node3-agent

# Or allow in System Preferences → Security & Privacy
```

### "No module named X"
- Rebuild with `--hidden-import=X` in PyInstaller
- Check if all dependencies are in requirements.txt

### Dashboard doesn't load
- Check if port 8080 is available
- Try different port: `DASHBOARD_PORT=8081`

## Preparing for Distribution

### 1. Create a Release Package

```bash
# Create release directory
mkdir -p releases/v1.0.0
cd releases/v1.0.0

# Copy executable
cp ../../dist/node3-agent .

# Copy README
cp ../../README.md .

# Create quick start guide
cat > QUICKSTART.md << 'EOF'
# Quick Start

1. Download `node3-agent`
2. Open Terminal
3. Navigate to download location
4. Run: `./node3-agent`
5. Open browser to: http://127.0.0.1:8080

For demo mode (no GPU):
Create `.env` file with:
SKIP_GPU_CHECK=true
EOF

# Create .env.example
cat > .env.example << 'EOF'
MARKETPLACE_URL=https://api.node-3.com
API_KEY=your_api_key_here
SOLANA_RPC_URL=https://api.devnet.solana.com
DASHBOARD_PORT=8080
SKIP_GPU_CHECK=false
EOF

# Create ZIP for distribution
cd ..
zip -r node3-agent-v1.0.0-macos.zip v1.0.0/
```

### 2. Test the Release Package

```bash
# Extract to clean location
cd /tmp
unzip ~/Desktop/node3agent/releases/node3-agent-v1.0.0-macos.zip
cd node3-agent-v1.0.0-macos/v1.0.0/

# Test
./node3-agent
```

## Automated Testing Script

Create a test script:

```bash
#!/bin/bash
# test_executable.sh

echo "Testing node3-agent executable..."

# Test 1: File exists and is executable
if [ ! -f "dist/node3-agent" ]; then
    echo "❌ Executable not found!"
    exit 1
fi
echo "✓ Executable found"

# Test 2: Is executable
if [ ! -x "dist/node3-agent" ]; then
    echo "Making executable..."
    chmod +x dist/node3-agent
fi
echo "✓ Executable has execute permissions"

# Test 3: File type
file_type=$(file dist/node3-agent)
echo "✓ File type: $file_type"

# Test 4: Check size
size=$(du -h dist/node3-agent | cut -f1)
echo "✓ File size: $size"

echo ""
echo "All basic checks passed!"
echo "Run './dist/node3-agent' to test execution"
```

## Next Steps

1. **Test locally** - Run the executable you just built
2. **Test in demo mode** - Verify dashboard works without GPU
3. **Create release package** - Package for distribution
4. **Upload to GitHub** - Create release with executable
5. **Test download** - Download from GitHub and test on clean system

