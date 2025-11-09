# Docker-Less Solution: Lima Integration

## Overview
Replace Docker requirement with **Lima** - a lightweight Docker alternative that can be bundled in DMG.

## Lima Benefits
- ✅ **50MB** vs Docker's 500MB
- ✅ **Docker API compatible** (drop-in replacement)
- ✅ **Can be embedded** in DMG
- ✅ **No GUI needed** (runs headless)
- ✅ **macOS optimized**

## Implementation

### Step 1: Modify docker_manager.py
Add Lima detection and auto-setup.

### Step 2: Bundle Lima Binary
Include Lima binary in DMG package structure.

### Step 3: First-Run Setup
Auto-configure Lima instance on first launch.

## Alternative: Native Execution (No Containers)

For even simpler distribution, we could run jobs natively with:
- Python subprocess isolation
- macOS sandboxing
- Resource limits (cgroups equivalent)
- File system isolation

**Pros:**
- Zero external dependencies
- Fastest startup
- Smallest DMG size

**Cons:**
- Less isolation than containers
- Requires careful security implementation

## Recommendation

**Hybrid Approach:**
1. Try Docker (if user has it) ✅
2. Try Lima (auto-install if needed) ✅  
3. Fall back to native execution (sandboxed) ✅

This gives users options while ensuring the DMG works out-of-the-box.

