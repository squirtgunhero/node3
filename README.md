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

### Download Pre-built Binary (Recommended)

**macOS:**
```bash
curl -L -o node3-agent https://github.com/YOUR_USERNAME/node3-agent/releases/latest/download/node3-agent-macos
chmod +x node3-agent
./node3-agent
```

**Linux:**
```bash
curl -L -o node3-agent https://github.com/YOUR_USERNAME/node3-agent/releases/latest/download/node3-agent-linux
chmod +x node3-agent
./node3-agent
```

**Windows:**
```powershell
Invoke-WebRequest -Uri "https://github.com/YOUR_USERNAME/node3-agent/releases/latest/download/node3-agent-windows.exe" -OutFile "node3-agent.exe"
.\node3-agent.exe
```

Visit http://localhost:8080 to see your dashboard.

## Installation

### Option 1: Pre-built Binary (Easiest)

1. Go to [Releases](https://github.com/YOUR_USERNAME/node3-agent/releases/latest)
2. Download the binary for your platform:
   - `node3-agent-macos` for macOS
   - `node3-agent-linux` for Linux
   - `node3-agent-windows.exe` for Windows
3. Make it executable (macOS/Linux): `chmod +x node3-agent`
4. Run it: `./node3-agent`

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
