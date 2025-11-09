# Bundling Lima in DMG

## Overview
Lima is a lightweight Docker alternative (~50MB) that can be bundled in the DMG, eliminating the need for users to install Docker Desktop.

## Implementation Complete ✅

The `docker_manager.py` now supports:
1. **Docker Desktop** (if user has it installed) - Primary option
2. **Lima** (auto-detected or bundled) - Fallback option
3. **Graceful degradation** (dashboard-only mode) - If neither available

## How It Works

### Runtime Detection Order:
1. Try Docker Desktop first (if installed)
2. Try Lima from PATH (if installed)
3. Try bundled Lima binary (`lima/bin/lima`)
4. Auto-setup Lima instance if needed
5. Fall back to dashboard-only mode

### Lima Auto-Setup:
- Checks for Lima instance `node3-agent`
- Creates instance if missing
- Configures Docker inside Lima VM
- Exposes Docker socket to host
- Agent uses Lima's Docker seamlessly

## Bundling Lima in DMG

### Step 1: Download Lima Binary

```bash
# Download Lima for macOS
# Check latest release: https://github.com/lima-vm/lima/releases
curl -L -o lima.tar.gz https://github.com/lima-vm/lima/releases/download/v0.21.0/lima-0.21.0-Darwin-x86_64.tar.gz

# Extract
tar -xzf lima.tar.gz
```

### Step 2: Organize in Project Structure

```
node3agent/
├── lima/
│   └── bin/
│       └── lima          # Lima binary
├── dist/
│   └── node3-agent.app/
└── ...
```

### Step 3: Update Build Script

Modify `build.py` to include Lima in DMG:

```python
def create_installer_macos():
    """Create macOS installer (.dmg) with Lima"""
    # ... existing code ...
    
    # Copy Lima binary to app bundle
    lima_dest = Path('dist/node3-agent.app/Contents/Resources/lima/bin')
    lima_dest.mkdir(parents=True, exist_ok=True)
    
    if Path('lima/bin/lima').exists():
        shutil.copy('lima/bin/lima', lima_dest / 'lima')
        os.chmod(lima_dest / 'lima', 0o755)
        print("✓ Lima binary included in bundle")
```

### Step 4: Update DMG Structure

The DMG should contain:
```
node³ Agent.app/
├── Contents/
│   ├── MacOS/
│   │   └── node3-agent
│   └── Resources/
│       └── lima/
│           └── bin/
│               └── lima
```

## User Experience

### First Launch:
1. User opens DMG and drags app to Applications
2. User launches node³ Agent
3. Agent detects no Docker → tries Lima
4. Finds bundled Lima → auto-creates instance
5. Lima VM starts → Docker available
6. Jobs can now execute! ✅

### Subsequent Launches:
- Agent detects Lima instance
- Starts Lima VM if needed
- Connects to Docker
- Ready to execute jobs

## Benefits

✅ **No Docker Desktop Required** - Users don't need to install Docker
✅ **Smaller Footprint** - 50MB Lima vs 500MB Docker Desktop
✅ **Auto-Setup** - Everything configured automatically
✅ **Seamless Experience** - Works just like Docker
✅ **Backward Compatible** - Still uses Docker if available

## Testing

### Test Lima Detection:
```bash
# Without Docker Desktop
# Agent should detect bundled Lima
python main.py

# Should see:
# "Lima not found in PATH"
# "Using bundled Lima: .../lima/bin/lima"
# "Setting up Lima instance 'node3-agent'..."
# "Lima Docker daemon is running"
```

### Test Job Execution:
```bash
# Start agent with marketplace
MARKETPLACE_URL=http://127.0.0.1:8000 python main.py

# Jobs should execute using Lima's Docker
```

## File Size Impact

- **Without Lima**: ~586MB (current executable)
- **With Lima**: ~636MB (+50MB for Lima binary)
- **Still smaller than**: Docker Desktop (500MB) + Agent (586MB) = 1GB+

## Next Steps

1. ✅ **Code Complete** - Lima support implemented
2. ⏳ **Download Lima** - Get Lima binary for macOS
3. ⏳ **Update Build** - Modify build.py to bundle Lima
4. ⏳ **Test DMG** - Build and test DMG with Lima
5. ⏳ **Update Docs** - Update README with Lima info

## Notes

- Lima instance persists between launches
- First setup takes ~2 minutes (downloads Ubuntu image)
- Subsequent launches are instant
- Lima VM uses ~8GB RAM / 50GB disk (configurable)

