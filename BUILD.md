# Quick Start Guide for Distribution

## Create Downloadable Executable

### Option 1: Simple Executable (Recommended)

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --name=node3-agent main.py

# Your executable will be in: dist/node3-agent (or dist/node3-agent.exe on Windows)
```

### Option 2: Using Build Script

```bash
# Install build dependencies
pip install pyinstaller build twine

# Build executable
python build.py --type exe
```

### Option 3: Python Package (pip installable)

```bash
# Build package
python setup.py sdist bdist_wheel

# Install locally
pip install dist/node3_agent-1.0.0-py3-none-any.whl
```

### Option 4: Docker Image

```bash
# Build Docker image
docker build -t node3-agent:latest .

# Run container
docker run -d -p 8080:8080 node3-agent:latest
```

## Distribution Files Created

After building, you'll find:

- **Executable**: `dist/node3-agent` (Linux/macOS) or `dist/node3-agent.exe` (Windows)
- **Python Package**: `dist/node3_agent-1.0.0.tar.gz` and `.whl` files
- **Docker Image**: `node3-agent:latest`

## Next Steps

1. **Test the executable** on a clean system
2. **Create GitHub Release** with executables
3. **Upload to PyPI** (if using Python package)
4. **Push to Docker Hub** (if using Docker)

See `DISTRIBUTION.md` for detailed instructions.

