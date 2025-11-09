# main.py
# node3 Agent - Version 1.0.0
VERSION = "1.0.0"

import asyncio
from loguru import logger
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Import modules
from gpu_detector import GPUDetector
from docker_manager import DockerManager
from job_manager import JobManager
from payment_module import PaymentModule
from dashboard import Dashboard

# Load environment variables
load_dotenv()

# Configuration
MARKETPLACE_URL = os.getenv("MARKETPLACE_URL", "https://api.node-3.com")
API_KEY = os.getenv("API_KEY", "")
WALLET_PATH = os.getenv("WALLET_PATH", "./wallet.json")
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))
SKIP_GPU_CHECK = os.getenv("SKIP_GPU_CHECK", "false").lower() == "true"

async def main():
    """Main application entry point"""
    
    logger.info("Starting node3 Agent...")
    
    try:
        # 1. Initialize GPU Detector
        logger.info("Initializing GPU detector...")
        gpu_detector = GPUDetector()
        gpus = gpu_detector.detect_gpus()
        
        if not gpus:
            if SKIP_GPU_CHECK:
                logger.warning("=" * 60)
                logger.warning("SKIP_GPU_CHECK enabled - running in demo mode without GPU")
                logger.warning("This mode is for testing only. Jobs will not execute.")
                logger.warning("=" * 60)
                # Create a dummy GPU info for demo mode
                from gpu_detector import GPUInfo, GPUType, ComputeFramework
                gpus = [GPUInfo(
                    index=0,
                    name='Demo GPU (No GPU Detected)',
                    vendor='Demo',
                    gpu_type=GPUType.UNKNOWN,
                    compute_framework=ComputeFramework.NONE,
                    total_memory=8192000000,  # 8GB
                    compute_capability=None
                )]
            else:
                logger.error("=" * 60)
                logger.error("No GPUs detected. Cannot continue.")
                logger.error("")
                logger.error("The node3 Agent supports GPUs from:")
                logger.error("  - NVIDIA (CUDA)")
                logger.error("  - AMD (ROCm)")
                logger.error("  - Intel (OpenCL)")
                logger.error("  - Apple Silicon (Metal)")
                logger.error("")
                logger.error("Please ensure:")
                logger.error("  - GPU drivers are installed")
                logger.error("  - Docker is running")
                logger.error("  - GPU is detected by your system")
                logger.error("")
                logger.error("For NVIDIA: Install drivers from https://www.nvidia.com/Download/index.aspx")
                logger.error("For AMD: Install ROCm from https://www.amd.com/en/support")
                logger.error("")
                logger.error("To test without GPU, set SKIP_GPU_CHECK=true in your .env file")
                logger.error("  (Note: Jobs will not execute in this mode)")
                logger.error("=" * 60)
                sys.exit(1)
            
        # Benchmark GPUs
        for gpu in gpus:
            logger.info(f"Benchmarking {gpu.name}...")
            benchmark = gpu_detector.benchmark_gpu(gpu.index)
            if benchmark:
                logger.info(f"Performance: {benchmark.get('tflops', 0):.2f} TFLOPS")
            
        # 2. Initialize Docker Manager
        logger.info("Initializing Docker manager...")
        # Pass GPU info to Docker manager for runtime selection
        gpu_info_dict = {
            'gpu_type': gpus[0].gpu_type.value if gpus else 'unknown',
            'compute_framework': gpus[0].compute_framework.value if gpus else 'none',
            'vendor': gpus[0].vendor if gpus else 'unknown'
        }
        try:
            docker_manager = DockerManager(gpu_info=gpu_info_dict)
        except Exception as e:
            logger.warning(f"Docker initialization failed: {e}")
            logger.warning("Continuing in demo mode without Docker...")
            # Create a dummy docker manager that won't execute jobs
            docker_manager = None
        
        # 3. Initialize Payment Module
        logger.info("Initializing payment module...")
        payment_module = PaymentModule(
            rpc_url=SOLANA_RPC_URL,
            wallet_path=WALLET_PATH
        )
        await payment_module.initialize()
        
        wallet_address = payment_module.get_wallet_address()
        balance = await payment_module.get_balance()
        
        logger.info(f"Wallet: {wallet_address}")
        logger.info(f"Balance: {balance} SOL")
        
        # 4. Initialize Job Manager (native execution by default, Docker optional)
        logger.info("Initializing job manager...")
        primary_gpu = gpus[0] if gpus else None
        
        if docker_manager is None:
            logger.info("Docker not available - using native execution (no installation needed!)")
        else:
            logger.info("Docker available - can use containers for enhanced isolation (optional)")
        
        job_manager = JobManager(
            marketplace_url=MARKETPLACE_URL,
            api_key=API_KEY,
            gpu_info={
                'name': primary_gpu.name if primary_gpu else 'Demo GPU',
                'vendor': primary_gpu.vendor if primary_gpu else 'Demo',
                'gpu_type': primary_gpu.gpu_type.value if primary_gpu else 'unknown',
                'compute_framework': primary_gpu.compute_framework.value if primary_gpu else 'none',
                'total_memory': primary_gpu.total_memory if primary_gpu else 0,
                'compute_capability': primary_gpu.compute_capability if primary_gpu else None
            },
            docker_manager=docker_manager,  # Optional - native execution works without it
            use_native_execution=True,  # Always enable native execution
            payment_module=payment_module  # For wallet address and payment tracking
        )
        
        # 5. Start Dashboard
        logger.info("Starting dashboard...")
        dashboard = Dashboard(
            gpu_detector=gpu_detector,
            job_manager=job_manager,
            payment_module=payment_module,
            port=DASHBOARD_PORT
        )
        
        # 6. Start all services
        logger.info("node3 Agent started successfully!")
        logger.info(f"Dashboard available at: http://127.0.0.1:{DASHBOARD_PORT}")
        
        # Run job manager and dashboard concurrently
        tasks = [dashboard.start()]
        if job_manager.is_running:
            tasks.append(job_manager.start())
        
        await asyncio.gather(*tasks)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        if 'payment_module' in locals():
            await payment_module.close()
        if 'gpu_detector' in locals():
            gpu_detector.shutdown()
            
if __name__ == "__main__":
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/node3_agent_{time:YYYY-MM-DD}.log",
        rotation="100 MB",
        retention="10 days",
        level="DEBUG"
    )
    
    # Run
    asyncio.run(main())

def main_entry():
    """Entry point for console script"""
    asyncio.run(main())

