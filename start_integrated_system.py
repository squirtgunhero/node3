#!/usr/bin/env python3
"""
Integrated node³ System Startup
================================
Starts the complete system: marketplace + agent + dashboard

This script:
1. Starts the production marketplace server
2. Waits for marketplace to be ready
3. Registers the GPU agent with the marketplace
4. Starts the agent to accept and execute jobs
5. Opens the dashboard

Usage:
    python start_integrated_system.py
    
Environment variables:
    MARKETPLACE_PORT=8000
    AGENT_PORT=8080
    DATABASE_URL=sqlite+aiosqlite:///./marketplace.db
    SOLANA_RPC_URL=https://api.devnet.solana.com
"""

import asyncio
import subprocess
import sys
import time
import os
from pathlib import Path
import httpx
from loguru import logger
import signal

# Configuration
MARKETPLACE_PORT = int(os.getenv("MARKETPLACE_PORT", "8000"))
AGENT_PORT = int(os.getenv("AGENT_PORT", "8080"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./marketplace.db")
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
MARKETPLACE_WALLET = os.getenv("MARKETPLACE_WALLET_PATH", "./marketplace_wallet.json")

# Process handles
marketplace_process = None
agent_process = None

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("\n🛑 Shutting down integrated system...")
    if marketplace_process:
        marketplace_process.terminate()
    if agent_process:
        agent_process.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


async def wait_for_service(url: str, name: str, max_attempts: int = 30):
    """Wait for a service to be ready"""
    logger.info(f"Waiting for {name} to be ready...")
    
    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=2.0)
                if response.status_code == 200:
                    logger.info(f"✓ {name} is ready!")
                    return True
        except Exception:
            pass
        
        await asyncio.sleep(1)
        
        if attempt % 5 == 0 and attempt > 0:
            logger.info(f"  Still waiting for {name}... ({attempt}/{max_attempts})")
    
    logger.error(f"✗ {name} failed to start")
    return False


async def register_agent_with_marketplace(gpu_info: dict):
    """Register the local GPU agent with the marketplace"""
    logger.info("Registering GPU agent with marketplace...")
    
    # Load wallet address
    import json
    try:
        with open('./wallet.json', 'r') as f:
            wallet_data = json.load(f)
            from solders.keypair import Keypair
            keypair = Keypair.from_base58_string(wallet_data['private_key'])
            wallet_address = str(keypair.pubkey())
    except Exception as e:
        logger.error(f"Error loading wallet: {e}")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:{MARKETPLACE_PORT}/api/agents/register",
                json={
                    'wallet_address': wallet_address,
                    'gpu_model': gpu_info['name'],
                    'gpu_vendor': gpu_info['vendor'],
                    'gpu_memory': gpu_info['total_memory'],
                    'compute_capability': {
                        'framework': gpu_info.get('compute_framework', 'unknown'),
                        'gpu_type': gpu_info.get('gpu_type', 'unknown')
                    }
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ Agent registered successfully!")
                logger.info(f"  Agent ID: {data['agent_id']}")
                logger.info(f"  GPU: {gpu_info['name']}")
                logger.info(f"  Wallet: {wallet_address[:8]}...{wallet_address[-8:]}")
                
                # Save API key to .env
                api_key = data['api_key']
                env_path = Path('.env')
                
                # Read existing .env or create new one
                env_content = {}
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        for line in f:
                            if '=' in line and not line.strip().startswith('#'):
                                key, value = line.strip().split('=', 1)
                                env_content[key] = value
                
                # Update API key and marketplace URL
                env_content['API_KEY'] = api_key
                env_content['MARKETPLACE_URL'] = f'http://localhost:{MARKETPLACE_PORT}'
                
                # Write back to .env
                with open(env_path, 'w') as f:
                    for key, value in env_content.items():
                        f.write(f'{key}={value}\n')
                
                logger.info(f"✓ API key saved to .env")
                
                return data
            else:
                logger.error(f"Failed to register agent: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        return None


async def detect_local_gpu():
    """Detect local GPU configuration"""
    logger.info("Detecting local GPU...")
    
    try:
        from gpu_detector import GPUDetector
        detector = GPUDetector()
        gpus = detector.detect_gpus()
        
        if not gpus:
            logger.warning("No GPU detected - will create demo GPU")
            from gpu_detector import GPUInfo, GPUType, ComputeFramework
            gpus = [GPUInfo(
                index=0,
                name='Demo GPU (No Hardware Detected)',
                vendor='Demo',
                gpu_type=GPUType.UNKNOWN,
                compute_framework=ComputeFramework.NONE,
                total_memory=8192000000,  # 8GB
                compute_capability=None
            )]
        
        gpu = gpus[0]
        logger.info(f"✓ GPU detected: {gpu.name}")
        logger.info(f"  Vendor: {gpu.vendor}")
        logger.info(f"  Memory: {gpu.total_memory / 1e9:.1f} GB")
        logger.info(f"  Framework: {gpu.compute_framework.value}")
        
        return {
            'name': gpu.name,
            'vendor': gpu.vendor,
            'gpu_type': gpu.gpu_type.value,
            'compute_framework': gpu.compute_framework.value,
            'total_memory': gpu.total_memory,
            'compute_capability': gpu.compute_capability
        }
        
    except Exception as e:
        logger.error(f"Error detecting GPU: {e}")
        return None


async def main():
    """Main startup sequence"""
    global marketplace_process, agent_process
    
    print("\n" + "="*60)
    print("  node³ Integrated System Startup")
    print("="*60 + "\n")
    
    # Check prerequisites
    logger.info("Checking prerequisites...")
    
    # Check if wallets exist
    if not Path('./wallet.json').exists():
        logger.error("✗ wallet.json not found - create agent wallet first")
        logger.info("  Run: python -m payment_module")
        return
    
    if not Path('./marketplace_wallet.json').exists():
        logger.warning("⚠ marketplace_wallet.json not found - creating...")
        os.system('cp wallet.json marketplace_wallet.json')
    
    # Set environment variables for marketplace
    os.environ['DATABASE_URL'] = DATABASE_URL
    os.environ['MARKETPLACE_WALLET_PATH'] = MARKETPLACE_WALLET
    os.environ['PORT'] = str(MARKETPLACE_PORT)
    os.environ['ENVIRONMENT'] = 'development'
    
    # 1. Start marketplace
    logger.info(f"\n📦 Starting production marketplace on port {MARKETPLACE_PORT}...")
    marketplace_process = subprocess.Popen(
        [sys.executable, 'production_marketplace.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Wait for marketplace
    if not await wait_for_service(f'http://localhost:{MARKETPLACE_PORT}/health', 'Marketplace'):
        logger.error("Failed to start marketplace")
        return
    
    # 2. Detect GPU
    gpu_info = await detect_local_gpu()
    if not gpu_info:
        logger.error("Failed to detect GPU")
        return
    
    # 3. Register agent
    registration = await register_agent_with_marketplace(gpu_info)
    if not registration:
        logger.error("Failed to register agent")
        return
    
    # 4. Start agent
    logger.info(f"\n🤖 Starting GPU agent on port {AGENT_PORT}...")
    os.environ['DASHBOARD_PORT'] = str(AGENT_PORT)
    os.environ['SKIP_GPU_CHECK'] = 'true'  # Allow demo mode if needed
    
    agent_process = subprocess.Popen(
        [sys.executable, 'main.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Wait for agent dashboard
    if not await wait_for_service(f'http://localhost:{AGENT_PORT}/api/status', 'Agent Dashboard'):
        logger.error("Failed to start agent")
        return
    
    # Success!
    print("\n" + "="*60)
    print("  ✅ node³ System is Running!")
    print("="*60)
    print(f"\n🏪 Marketplace API:     http://localhost:{MARKETPLACE_PORT}")
    print(f"🤖 Agent Dashboard:     http://localhost:{AGENT_PORT}")
    print(f"🏪 Marketplace Browser: http://localhost:{AGENT_PORT}/marketplace")
    print("\n📋 Next Steps:")
    print("  1. Open agent dashboard to monitor your GPU")
    print("  2. Post a test job to the marketplace:")
    print(f"     python marketplace_admin.py create-job --reward 0.001")
    print("  3. Watch your agent automatically accept and execute the job")
    print("  4. Receive SOL payment upon completion")
    print("\n💡 Tips:")
    print("  • View marketplace stats: python marketplace_admin.py stats")
    print("  • Create test jobs: python marketplace_admin.py create-test-jobs --count 5")
    print("  • Monitor payments: python marketplace_admin.py payment-history")
    print("\nPress Ctrl+C to stop the system\n")
    
    # Keep running and show logs
    try:
        while True:
            await asyncio.sleep(1)
            
            # Check if processes are still running
            if marketplace_process.poll() is not None:
                logger.error("Marketplace process died!")
                break
            if agent_process.poll() is not None:
                logger.error("Agent process died!")
                break
                
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
    finally:
        if marketplace_process:
            marketplace_process.terminate()
            marketplace_process.wait(timeout=5)
        if agent_process:
            agent_process.terminate()
            agent_process.wait(timeout=5)
        logger.info("✓ System stopped")


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

