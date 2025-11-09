# Docker Alternatives for DMG Distribution

## Problem
Docker Desktop (~500MB+) cannot be bundled in DMG due to:
- Size constraints
- Licensing restrictions
- Installation complexity
- System requirements

## Solution Options

### Option 1: Use Lima/Colima (Recommended) ⭐
**Lima** or **Colima** are lightweight Docker alternatives for macOS that can be bundled.

**Pros:**
- Much smaller (~50MB vs 500MB)
- Can be embedded in DMG
- Provides Docker API compatibility
- No GUI required
- Works without Docker Desktop

**Implementation:**
```python
# Check for Lima/Colima instead of Docker
# Falls back to Docker if available
# Auto-installs Lima if not present
```

### Option 2: Native Process Execution (Simpler)
Run jobs directly using Python subprocess with sandboxing.

**Pros:**
- No Docker required
- Smaller footprint
- Faster startup
- Works on all platforms

**Cons:**
- Less isolation than containers
- Requires careful security implementation
- GPU access more complex

### Option 3: Embedded containerd Runtime
Bundle containerd (lightweight container runtime) directly.

**Pros:**
- Full container isolation
- Smaller than Docker Desktop
- Industry standard

**Cons:**
- Still ~100MB+
- More complex to bundle
- Requires system integration

### Option 4: Hybrid Approach
- Try Docker first (if user has it)
- Fall back to Lima/Colima (auto-install)
- Fall back to native execution (sandboxed)

## Recommended: Lima Integration

Lima is perfect for macOS DMG distribution:
- **Size**: ~50MB vs Docker's 500MB
- **Installation**: Can be embedded
- **Compatibility**: Docker API compatible
- **No GUI**: Runs headless

## Implementation Plan

1. **Add Lima detection** to `docker_manager.py`
2. **Auto-install Lima** if Docker not available
3. **Use Lima runtime** for container execution
4. **Bundle Lima binary** in DMG (or download on first run)

## Next Steps

1. Modify `docker_manager.py` to support Lima
2. Add Lima binary to DMG package
3. Update documentation
4. Test with Lima runtime

