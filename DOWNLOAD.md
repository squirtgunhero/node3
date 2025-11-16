# Download Node3 Agent

Choose your platform and follow the instructions below.

## macOS

### One-liner Install
```bash
curl -L -o node3-agent https://github.com/YOUR_USERNAME/node3-agent/releases/latest/download/node3-agent-macos && chmod +x node3-agent && ./node3-agent
```

### Step-by-step
1. Download the binary:
   ```bash
   curl -L -o node3-agent https://github.com/YOUR_USERNAME/node3-agent/releases/latest/download/node3-agent-macos
   ```

2. Make it executable:
   ```bash
   chmod +x node3-agent
   ```

3. Run it:
   ```bash
   ./node3-agent
   ```

4. Open your browser to: http://localhost:8080

### macOS Security Note
If you get a security warning, run:
```bash
xattr -d com.apple.quarantine node3-agent
```

## Linux

### One-liner Install
```bash
curl -L -o node3-agent https://github.com/YOUR_USERNAME/node3-agent/releases/latest/download/node3-agent-linux && chmod +x node3-agent && ./node3-agent
```

### Step-by-step
1. Download the binary:
   ```bash
   curl -L -o node3-agent https://github.com/YOUR_USERNAME/node3-agent/releases/latest/download/node3-agent-linux
   ```

2. Make it executable:
   ```bash
   chmod +x node3-agent
   ```

3. Run it:
   ```bash
   ./node3-agent
   ```

4. Open your browser to: http://localhost:8080

## Windows

### PowerShell (Recommended)
```powershell
# Download
Invoke-WebRequest -Uri "https://github.com/YOUR_USERNAME/node3-agent/releases/latest/download/node3-agent-windows.exe" -OutFile "node3-agent.exe"

# Run
.\node3-agent.exe
```

### Manual Download
1. Go to: https://github.com/YOUR_USERNAME/node3-agent/releases/latest
2. Download `node3-agent-windows.exe`
3. Double-click to run

### Windows Defender Note
If Windows Defender blocks it:
1. Click "More info"
2. Click "Run anyway"

This is normal for unsigned executables.

## Verify Download (Optional)

Download the checksums file:
```bash
curl -L -o checksums.txt https://github.com/YOUR_USERNAME/node3-agent/releases/latest/download/checksums.txt
```

Verify your download:
```bash
# macOS/Linux
sha256sum -c checksums.txt

# Windows (PowerShell)
Get-FileHash node3-agent-windows.exe -Algorithm SHA256
```

## System Requirements

### All Platforms
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 1GB free space
- **Network**: Internet connection

### GPU Requirements
At least one of:
- **NVIDIA GPU**: CUDA-capable (GTX 900 series or newer)
  - Install [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
- **AMD GPU**: ROCm-capable
  - Install [ROCm drivers](https://rocm.docs.amd.com/)
- **Apple Silicon**: M1/M2/M3
  - Built-in Metal support (no installation needed)
- **Intel GPU**: OpenCL-capable
  - Install [Intel OpenCL drivers](https://www.intel.com/content/www/us/en/developer/tools/opencl-sdk/overview.html)

## Docker (Optional)

For containerized job execution:

### macOS
```bash
brew install --cask docker
```

### Linux
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Enable Docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### Windows
Download [Docker Desktop](https://www.docker.com/products/docker-desktop/)

## Troubleshooting

### Binary won't run
**macOS:**
```bash
xattr -d com.apple.quarantine node3-agent
```

**Linux:**
```bash
chmod +x node3-agent
```

**Windows:** Run as Administrator

### Can't connect to dashboard
Check if port 8080 is available:
```bash
# macOS/Linux
lsof -i :8080

# Windows
netstat -ano | findstr :8080
```

### GPU not detected
1. Verify GPU drivers are installed:
   ```bash
   # NVIDIA
   nvidia-smi
   
   # AMD
   rocm-smi
   
   # Apple Silicon (should show your GPU)
   system_profiler SPDisplaysDataType
   ```

2. Restart the agent after installing drivers

### Need help?
- [Documentation](https://github.com/YOUR_USERNAME/node3-agent)
- [Open an issue](https://github.com/YOUR_USERNAME/node3-agent/issues)

## Next Steps

Once running:
1. Open http://localhost:8080
2. View your GPU status
3. Monitor for available jobs
4. Check your earnings

## Updates

The agent checks for updates automatically. To manually update:

```bash
# Stop the current agent (Ctrl+C)

# Download latest version (same command as initial download)
curl -L -o node3-agent https://github.com/YOUR_USERNAME/node3-agent/releases/latest/download/node3-agent-macos

# Run
./node3-agent
```

## Uninstall

Simply delete the binary:
```bash
rm node3-agent
```

Optional: Remove config and logs
```bash
rm -rf ~/.node3-agent
rm -rf logs/
rm wallet.json
```

