# Distribution Guide

This guide explains how to create downloadable distributions of the node3 agent for different platforms.

## Prerequisites

Install build dependencies:

```bash
pip install pyinstaller build twine
```

## Build Options

### 1. Standalone Executable (Recommended for most users)

Creates a single executable file that includes everything:

```bash
# Build executable
python build.py --type exe

# Or manually with PyInstaller
pyinstaller --onefile --name=node3-agent main.py
```

**Output:** `dist/node3-agent` (or `dist/node3-agent.exe` on Windows)

**Pros:**
- Single file, easy to distribute
- No Python installation required
- Works on Windows, macOS, Linux

**Cons:**
- Larger file size (~50-100MB)
- Slower startup time
- Platform-specific builds needed

### 2. Docker Image (Recommended for servers)

Containerized distribution:

```bash
# Build Docker image
docker build -t node3-agent:latest .

# Run container
docker run -d \
  --name node3-agent \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/wallet.json:/app/wallet.json \
  node3-agent:latest
```

**Output:** Docker image `node3-agent:latest`

**Pros:**
- Consistent environment
- Easy deployment
- Works everywhere Docker runs

**Cons:**
- Requires Docker installed
- GPU access requires GPU runtime setup

### 3. Python Package (pip installable)

Create a pip-installable package:

```bash
# Build package
python build.py --type pip

# Or manually
python setup.py sdist bdist_wheel

# Install locally
pip install dist/node3_agent-1.0.0-py3-none-any.whl

# Or upload to PyPI
twine upload dist/*
```

**Output:** `dist/node3-agent-1.0.0.tar.gz` and `.whl` files

**Pros:**
- Easy to install: `pip install node3-agent`
- Can be uploaded to PyPI
- Standard Python packaging

**Cons:**
- Requires Python installed
- Users need to install dependencies

### 4. Platform-Specific Installers

#### macOS (.dmg)

```bash
python build.py --type macos
```

Creates a `.dmg` installer file.

#### Windows (.exe installer)

Requires Inno Setup or NSIS:

```bash
python build.py --type windows
```

#### Linux (.deb package)

```bash
python build.py --type deb
```

Creates a `.deb` package for Debian/Ubuntu.

## Build Scripts

### Quick Build

```bash
# Build executable for current platform
python build.py

# Build all distribution types
python build.py --type all
```

### Advanced PyInstaller Options

Edit `node3-agent.spec` for custom builds:

```python
# For windowed mode (no console)
console=False

# For console mode (shows terminal)
console=True

# Add additional data files
datas=[('templates', 'templates'), ('config', 'config')]
```

## Distribution Checklist

Before distributing:

- [ ] Test executable on clean system
- [ ] Verify all dependencies are included
- [ ] Test GPU detection works
- [ ] Test dashboard loads correctly
- [ ] Create release notes
- [ ] Sign executables (macOS/Windows)
- [ ] Create installer if needed
- [ ] Upload to distribution platform

## File Structure After Build

```
dist/
├── node3-agent          # Executable (Linux/macOS)
├── node3-agent.exe      # Executable (Windows)
├── node3-agent.dmg      # macOS installer
├── node3-agent.deb      # Debian package
├── node3_agent-1.0.0.tar.gz    # Source distribution
└── node3_agent-1.0.0-py3-none-any.whl  # Wheel package
```

## Platform-Specific Notes

### macOS
- May need to sign executable for Gatekeeper
- Use `codesign` to sign: `codesign --sign "Developer ID" dist/node3-agent`
- Create .app bundle for better macOS integration

### Windows
- Use Inno Setup or NSIS for installer
- Sign executable with Authenticode certificate
- Consider adding to Windows startup

### Linux
- Create .deb for Debian/Ubuntu
- Create .rpm for RedHat/Fedora
- Consider creating AppImage for universal Linux package

## Publishing

### GitHub Releases

1. Create release tag:
```bash
git tag v1.0.0
git push origin v1.0.0
```

2. Build executables for all platforms
3. Upload to GitHub Releases page

### PyPI

```bash
# Build package
python setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*
```

Users can then install with:
```bash
pip install node3-agent
```

## Docker Hub

```bash
# Build and tag
docker build -t node3/agent:latest .
docker tag node3/agent:latest node3/agent:v1.0.0

# Push to Docker Hub
docker push node3/agent:latest
docker push node3/agent:v1.0.0
```

## Size Optimization

To reduce executable size:

1. Use UPX compression (enabled in spec file)
2. Exclude unused modules
3. Use `--strip` flag
4. Consider splitting into library + executable

## Testing Distributions

Test on clean systems:

```bash
# Create test VM
# Install only OS
# Copy executable
# Test installation
# Verify functionality
```

## Next Steps

1. Choose distribution method(s)
2. Set up CI/CD for automated builds
3. Create release documentation
4. Set up update mechanism (optional)
