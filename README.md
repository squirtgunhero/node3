# node3 Agent

A cross-platform application that allows GPU owners to monetize their idle compute capacity by connecting to the node3 decentralized marketplace.

## Features

- **GPU Detection**: Automatically detects and benchmarks GPUs from multiple vendors
  - **NVIDIA** GPUs (CUDA)
  - **AMD** GPUs (ROCm)
  - **Intel** GPUs (OpenCL)
  - **Apple Silicon** GPUs (Metal)
- **Job Execution**: Runs compute jobs natively (no Docker required!) with optional container support
- **Marketplace Integration**: Connects to node3 marketplace to receive jobs
- **Solana Payments**: Real-time payment settlement via Solana blockchain
- **Real-time Dashboard**: Web-based dashboard for monitoring and control
- **Background Operation**: Runs without interfering with normal computer use

## Requirements

- Python 3.10+ (or standalone executable - no Python needed!)
- GPU from one of these vendors (optional - CPU jobs also supported):
  - **NVIDIA** (with CUDA support)
  - **AMD** (with ROCm support)
  - **Intel** (with OpenCL support)
  - **Apple Silicon** (Metal support)
- 8GB+ RAM
- 50GB+ disk space

**No Docker Required!** ✅  
The agent runs jobs natively out of the box. Docker/Lima are optional enhancements for better isolation.

## Installation

### Quick Start (macOS) - Download & Run

**Easiest way to get started:**

1. **Download the DMG installer:**
   - Latest release: [Download node3-agent-installer.dmg](https://github.com/node3/agent/releases/latest)
   - Or build from source (see below)

2. **Install:**
   - Double-click `node3-agent-installer.dmg`
   - Drag `node3-agent.app` to Applications folder
   - Open from Applications

3. **Run:**
   - Double-click `node3-agent.app` in Applications
   - Dashboard opens at http://127.0.0.1:8080
   - No Python or Docker installation needed!

**Note:** First run may show a security warning. Go to System Preferences → Security & Privacy → Click "Open Anyway"

---

### Build from Source

### 1. Install System Dependencies

**For NVIDIA GPUs:**
- CUDA Drivers: https://developer.nvidia.com/cuda-downloads
- NVIDIA Docker Runtime: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

**For AMD GPUs:**
- ROCm: https://www.amd.com/en/support
- ROCm Docker Runtime

**For Intel GPUs:**
- OpenCL drivers (usually included with drivers)
- Intel oneAPI toolkit (optional)

**For Apple Silicon:**
- Metal support is built-in (no additional drivers needed)

**Optional - Docker/Lima (for enhanced isolation):**
- If you want container-based job execution, you can install Docker Desktop
- Or use Lima (lightweight alternative, can be bundled)
- **Not required** - native execution works perfectly without it!

### 2. Setup Python Environment

```bash
# Clone repository
git clone https://github.com/node3/agent.git
cd agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Agent

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# - MARKETPLACE_URL: Your marketplace API endpoint
# - API_KEY: Your API key from marketplace
# - SOLANA_RPC_URL: Solana RPC endpoint (use devnet for testing)
```

## Usage

```bash
# Run the agent
python main.py
```

The dashboard will be available at: http://127.0.0.1:8080

## Project Structure

```
node3-agent/
├── main.py                 # Main entry point
├── gpu_detector.py         # GPU detection and monitoring
├── docker_manager.py       # Docker container management
├── job_manager.py          # Job lifecycle management
├── payment_module.py       # Solana wallet and payments
├── dashboard.py            # Web dashboard server
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── templates/
│   └── index.html         # Dashboard HTML template
└── logs/                  # Log files
```

## Configuration

Key environment variables:

- `MARKETPLACE_URL`: Marketplace API endpoint
- `API_KEY`: Your API key
- `WALLET_PATH`: Path to wallet file (default: ./wallet.json)
- `SOLANA_RPC_URL`: Solana RPC endpoint
- `DASHBOARD_PORT`: Dashboard port (default: 8080)
- `GPU_INDEX`: GPU to use (default: 0)
- `MAX_CONCURRENT_JOBS`: Maximum concurrent jobs (default: 1)
- `SKIP_GPU_CHECK`: Set to `true` to run in demo mode without GPU (for testing only)

## Security

- Jobs run in isolated Docker containers
- No network access for containers
- Resource limits enforced
- Wallet stored locally and encrypted
- Private keys never leave your machine

## Troubleshooting

### No GPUs detected
- Ensure GPU drivers are installed for your vendor:
  - **NVIDIA**: Install drivers from https://www.nvidia.com/Download/index.aspx
  - **AMD**: Install ROCm from https://www.amd.com/en/support
  - **Intel**: OpenCL drivers are usually included with graphics drivers
  - **Apple Silicon**: No drivers needed (Metal is built-in)
- Check GPU is detected by your system:
  - **macOS**: `system_profiler SPDisplaysDataType`
  - **Linux**: `lspci | grep -i vga`
  - **Windows**: Device Manager
- Verify Docker GPU runtime is installed:
  - **NVIDIA**: `docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi`
  - **AMD**: Check rocm-docker installation
- **For testing**: Set `SKIP_GPU_CHECK=true` in `.env` to run in demo mode (jobs will not execute)

### Docker errors
- Ensure Docker daemon is running
- Check nvidia-docker runtime is installed
- Verify GPU access: `docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi`

### Marketplace connection issues
- Verify MARKETPLACE_URL is correct
- Check API_KEY is valid
- Ensure network connectivity

## Development

### Running Tests

```bash
# Unit tests
pytest tests/

# Integration tests
pytest tests/integration/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

For issues and questions:
- GitHub Issues: https://github.com/node3/agent/issues
- Documentation: https://docs.node-3.com
- Community: https://discord.gg/node3

