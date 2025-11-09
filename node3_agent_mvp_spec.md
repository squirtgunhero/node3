# node3 Agent MVP - Technical Specification

## Project Overview

Build the **node3 Agent** - a cross-platform application that allows GPU owners to monetize their idle compute capacity by connecting to the node3 decentralized marketplace.

**Status:** MVP Phase 1 - GPU Compute Only  
**Target Launch:** 90 days  
**Primary Goal:** Prove marketplace model with 100-500 beta users

---

## Product Requirements

### Core Functionality

**The node3 agent must:**

1. **Detect GPU hardware** on the user's machine
2. **Benchmark performance** to determine earning potential
3. **Connect to node3 marketplace** to receive compute jobs
4. **Execute jobs securely** in isolated containers
5. **Report results** back to the marketplace
6. **Handle payments** via Solana blockchain
7. **Provide real-time dashboard** showing earnings and status
8. **Run in background** without interfering with normal computer use

### Success Criteria

- Agent runs on Windows, Mac, and Linux
- Detects NVIDIA GPUs (RTX series priority)
- Successfully executes AI/ML inference jobs
- <5 minute setup time for non-technical users
- <5% CPU overhead when idle
- 99%+ job completion rate
- Real-time payment settlement via Solana

---

## Technical Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   USER'S MACHINE                     │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │          node3 Agent (Python)               │    │
│  │                                             │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │   GPU Detection Module                │  │    │
│  │  │   - nvidia-smi interface              │  │    │
│  │  │   - CUDA capability check             │  │    │
│  │  │   - Benchmark GPU performance         │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  │                                             │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │   Job Manager                         │  │    │
│  │  │   - Poll marketplace for jobs         │  │    │
│  │  │   - Job queue management              │  │    │
│  │  │   - Result reporting                  │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  │                                             │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │   Docker Container Manager            │  │    │
│  │  │   - Isolated job execution            │  │    │
│  │  │   - Resource limits (GPU, RAM, CPU)   │  │    │
│  │  │   - Security sandboxing               │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  │                                             │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │   Payment Module (Solana)             │  │    │
│  │  │   - Wallet integration                │  │    │
│  │  │   - Payment receipt                   │  │    │
│  │  │   - Balance tracking                  │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  │                                             │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │   Local Dashboard (FastAPI + Web UI)  │  │    │
│  │  │   - Real-time earnings                │  │    │
│  │  │   - Job history                       │  │    │
│  │  │   - Performance metrics               │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
                         │
                         │ HTTPS / WebSocket
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              node3 Marketplace (Cloud)               │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Job Queue   │  │  Matching     │  │  Payment  │ │
│  │  Service     │  │  Engine       │  │  Service  │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │         Solana Smart Contracts                │  │
│  │         - Escrow payments                     │  │
│  │         - Automatic settlement                │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Agent (Client-Side)

**Language:** Python 3.10+

**Core Dependencies:**
```python
# GPU Detection & Management
pynvml              # NVIDIA GPU management
py3nvml             # Python NVIDIA management
torch               # For CUDA checks and GPU operations

# Container Management
docker              # Docker SDK for Python
docker-compose      # Container orchestration

# API Communication
httpx               # Async HTTP client
websockets          # Real-time communication with marketplace
aiohttp             # Async HTTP server for local dashboard

# Blockchain
solana              # Solana Python SDK
solders             # Solana Rust bindings for Python

# Web Interface
fastapi             # Local web server for dashboard
uvicorn             # ASGI server
jinja2              # HTML templates
websockets          # Real-time updates to dashboard

# Utilities
pydantic            # Data validation
python-dotenv       # Configuration management
psutil              # System monitoring
schedule            # Job scheduling
loguru              # Logging
```

**Why Python?**
- Fast development for MVP
- Excellent GPU/ML library support
- Easy to package for all platforms
- Large community for troubleshooting

### Marketplace Backend (Server-Side)

**For MVP, we'll use a simplified backend:**

**Language:** Python (FastAPI) or Node.js (Express)

**Infrastructure:**
- **Hosting:** Railway, Render, or AWS (minimal setup)
- **Database:** PostgreSQL (managed service)
- **Queue:** Redis for job queue
- **Blockchain:** Solana Devnet (testnet) → Mainnet after validation

---

## Component Specifications

### 1. GPU Detection Module

**Purpose:** Identify and benchmark GPU hardware

**Features:**
- Detect NVIDIA GPUs via `nvidia-smi`
- Get GPU specs: model, VRAM, CUDA cores, compute capability
- Benchmark performance (TFLOPS, memory bandwidth)
- Continuous monitoring of GPU utilization
- Detect if GPU is available or in use

**Implementation:**

```python
# gpu_detector.py

import pynvml
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class GPUInfo:
    """GPU hardware information"""
    index: int
    name: str
    uuid: str
    total_memory: int  # bytes
    compute_capability: tuple  # (major, minor)
    cuda_cores: int
    clock_speed: int  # MHz
    memory_clock: int  # MHz
    
class GPUDetector:
    """Detect and monitor NVIDIA GPUs"""
    
    def __init__(self):
        self.initialized = False
        self.gpus: List[GPUInfo] = []
        
    def initialize(self) -> bool:
        """Initialize NVIDIA Management Library"""
        try:
            pynvml.nvmlInit()
            self.initialized = True
            logger.info("NVML initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize NVML: {e}")
            return False
            
    def detect_gpus(self) -> List[GPUInfo]:
        """Detect all available GPUs"""
        if not self.initialized:
            if not self.initialize():
                return []
                
        try:
            device_count = pynvml.nvmlDeviceGetCount()
            logger.info(f"Found {device_count} GPU(s)")
            
            self.gpus = []
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                gpu_info = GPUInfo(
                    index=i,
                    name=pynvml.nvmlDeviceGetName(handle),
                    uuid=pynvml.nvmlDeviceGetUUID(handle),
                    total_memory=pynvml.nvmlDeviceGetMemoryInfo(handle).total,
                    compute_capability=pynvml.nvmlDeviceGetCudaComputeCapability(handle),
                    cuda_cores=self._get_cuda_cores(handle),
                    clock_speed=pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS),
                    memory_clock=pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                )
                
                self.gpus.append(gpu_info)
                logger.info(f"GPU {i}: {gpu_info.name}")
                
            return self.gpus
            
        except Exception as e:
            logger.error(f"Error detecting GPUs: {e}")
            return []
            
    def _get_cuda_cores(self, handle) -> int:
        """Estimate CUDA cores based on GPU architecture"""
        # This is a simplified estimation
        # In production, use a lookup table for accurate counts
        compute_capability = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
        sm_count = pynvml.nvmlDeviceGetNumGpuCores(handle)
        
        # Cores per SM varies by architecture
        cores_per_sm_map = {
            (7, 5): 64,  # Turing
            (8, 0): 64,  # Ampere
            (8, 6): 128, # Ampere (GA102)
            (8, 9): 128, # Ada Lovelace
        }
        
        cores_per_sm = cores_per_sm_map.get(compute_capability, 64)
        return sm_count * cores_per_sm
        
    def get_gpu_utilization(self, gpu_index: int = 0) -> Dict:
        """Get current GPU utilization metrics"""
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
            
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
            
            return {
                'gpu_utilization': utilization.gpu,  # Percentage
                'memory_utilization': utilization.memory,  # Percentage
                'memory_used': memory_info.used,
                'memory_free': memory_info.free,
                'temperature': temperature,  # Celsius
                'power_usage': power  # Watts
            }
            
        except Exception as e:
            logger.error(f"Error getting GPU utilization: {e}")
            return {}
            
    def is_gpu_available(self, gpu_index: int = 0, threshold: int = 20) -> bool:
        """Check if GPU is available for work (not heavily utilized)"""
        util = self.get_gpu_utilization(gpu_index)
        if not util:
            return False
            
        # Consider GPU available if utilization is below threshold
        return util['gpu_utilization'] < threshold
        
    def benchmark_gpu(self, gpu_index: int = 0) -> Dict:
        """Run simple benchmark to estimate GPU performance"""
        import torch
        import time
        
        if not torch.cuda.is_available():
            logger.error("CUDA not available for benchmarking")
            return {}
            
        try:
            # Simple matrix multiplication benchmark
            device = torch.device(f'cuda:{gpu_index}')
            size = 10000
            
            # Warm up
            a = torch.randn(size, size, device=device)
            b = torch.randn(size, size, device=device)
            torch.matmul(a, b)
            torch.cuda.synchronize()
            
            # Benchmark
            iterations = 10
            start = time.time()
            
            for _ in range(iterations):
                c = torch.matmul(a, b)
                torch.cuda.synchronize()
                
            end = time.time()
            elapsed = end - start
            
            # Calculate TFLOPS
            # Matrix multiply: 2 * size^3 operations
            operations = 2 * (size ** 3) * iterations
            tflops = (operations / elapsed) / 1e12
            
            logger.info(f"GPU {gpu_index} benchmark: {tflops:.2f} TFLOPS")
            
            return {
                'tflops': tflops,
                'elapsed_time': elapsed,
                'iterations': iterations
            }
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            return {}
            
    def shutdown(self):
        """Cleanup NVML"""
        if self.initialized:
            try:
                pynvml.nvmlShutdown()
                logger.info("NVML shutdown successfully")
            except Exception as e:
                logger.error(f"Error shutting down NVML: {e}")
```

**Usage:**
```python
detector = GPUDetector()
gpus = detector.detect_gpus()

for gpu in gpus:
    print(f"{gpu.name}: {gpu.total_memory / 1e9:.1f}GB VRAM")
    
# Check if GPU is available
if detector.is_gpu_available(0):
    print("GPU is available for work")
    
# Run benchmark
benchmark = detector.benchmark_gpu(0)
print(f"Performance: {benchmark['tflops']:.2f} TFLOPS")
```

---

### 2. Job Manager Module

**Purpose:** Poll marketplace for jobs, manage job queue, execute jobs, report results

**Features:**
- Connect to marketplace API
- Poll for available jobs matching GPU capabilities
- Download job specifications and data
- Queue management (FIFO with priority)
- Execute jobs in Docker containers
- Upload results
- Handle retries and errors

**Implementation:**

```python
# job_manager.py

import asyncio
import httpx
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from loguru import logger

class JobStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UPLOADING = "uploading"

@dataclass
class Job:
    """Job specification"""
    job_id: str
    job_type: str  # "inference", "training", "rendering"
    docker_image: str
    gpu_memory_required: int  # bytes
    estimated_duration: int  # seconds
    reward: float  # in SOL or USD
    input_data_url: str
    output_upload_url: str
    command: List[str]
    environment: Dict[str, str]
    timeout: int  # seconds
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class JobManager:
    """Manage job lifecycle from marketplace to execution"""
    
    def __init__(self, 
                 marketplace_url: str,
                 api_key: str,
                 gpu_info: Dict,
                 docker_manager):
        self.marketplace_url = marketplace_url
        self.api_key = api_key
        self.gpu_info = gpu_info
        self.docker_manager = docker_manager
        self.active_jobs: List[Job] = []
        self.job_history: List[Job] = []
        self.is_running = False
        
    async def start(self):
        """Start the job manager loop"""
        self.is_running = True
        logger.info("Job manager started")
        
        while self.is_running:
            try:
                # Poll for new jobs
                await self.poll_marketplace()
                
                # Process queued jobs
                await self.process_jobs()
                
                # Wait before next poll
                await asyncio.sleep(10)  # Poll every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in job manager loop: {e}")
                await asyncio.sleep(30)
                
    async def poll_marketplace(self):
        """Poll marketplace for available jobs"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.marketplace_url}/api/jobs/available",
                    json={
                        'gpu_model': self.gpu_info['name'],
                        'gpu_memory': self.gpu_info['total_memory'],
                        'compute_capability': self.gpu_info['compute_capability'],
                        'max_concurrent_jobs': 1  # MVP: one job at a time
                    },
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    jobs_data = response.json()
                    
                    for job_data in jobs_data.get('jobs', []):
                        job = Job(
                            job_id=job_data['job_id'],
                            job_type=job_data['job_type'],
                            docker_image=job_data['docker_image'],
                            gpu_memory_required=job_data['gpu_memory_required'],
                            estimated_duration=job_data['estimated_duration'],
                            reward=job_data['reward'],
                            input_data_url=job_data['input_data_url'],
                            output_upload_url=job_data['output_upload_url'],
                            command=job_data['command'],
                            environment=job_data.get('environment', {}),
                            timeout=job_data.get('timeout', 3600),
                            created_at=datetime.now()
                        )
                        
                        # Accept the job
                        await self.accept_job(job)
                        
                else:
                    logger.warning(f"Failed to poll marketplace: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error polling marketplace: {e}")
            
    async def accept_job(self, job: Job):
        """Accept a job from the marketplace"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.marketplace_url}/api/jobs/{job.job_id}/accept",
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.active_jobs.append(job)
                    logger.info(f"Accepted job {job.job_id}: {job.job_type} - {job.reward} SOL")
                else:
                    logger.warning(f"Failed to accept job {job.job_id}: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error accepting job: {e}")
            
    async def process_jobs(self):
        """Process active jobs"""
        for job in self.active_jobs[:]:  # Copy list to allow modification during iteration
            try:
                if job.status == JobStatus.PENDING:
                    await self.execute_job(job)
                    
            except Exception as e:
                logger.error(f"Error processing job {job.job_id}: {e}")
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                await self.report_job_failure(job)
                
    async def execute_job(self, job: Job):
        """Execute a job in Docker container"""
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            
            logger.info(f"Executing job {job.job_id}")
            
            # Download input data
            await self.download_input_data(job)
            
            # Run Docker container
            result = await self.docker_manager.run_job(
                image=job.docker_image,
                command=job.command,
                environment=job.environment,
                gpu_id=0,  # MVP: use first GPU
                timeout=job.timeout,
                volumes={
                    '/tmp/node3_input': {'bind': '/input', 'mode': 'ro'},
                    '/tmp/node3_output': {'bind': '/output', 'mode': 'rw'}
                }
            )
            
            if result['success']:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                
                # Upload results
                await self.upload_results(job)
                
                # Report success
                await self.report_job_success(job)
                
                # Move to history
                self.active_jobs.remove(job)
                self.job_history.append(job)
                
                logger.info(f"Job {job.job_id} completed successfully")
                
            else:
                raise Exception(f"Job execution failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            await self.report_job_failure(job)
            self.active_jobs.remove(job)
            self.job_history.append(job)
            
    async def download_input_data(self, job: Job):
        """Download input data for job"""
        logger.info(f"Downloading input data for job {job.job_id}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(job.input_data_url, timeout=300.0)
            
            if response.status_code == 200:
                # Save to /tmp/node3_input/
                import os
                os.makedirs('/tmp/node3_input', exist_ok=True)
                
                with open(f'/tmp/node3_input/{job.job_id}_input.tar.gz', 'wb') as f:
                    f.write(response.content)
                    
                # Extract if compressed
                import tarfile
                with tarfile.open(f'/tmp/node3_input/{job.job_id}_input.tar.gz', 'r:gz') as tar:
                    tar.extractall(f'/tmp/node3_input/')
                    
                logger.info(f"Input data downloaded for job {job.job_id}")
            else:
                raise Exception(f"Failed to download input data: {response.status_code}")
                
    async def upload_results(self, job: Job):
        """Upload job results"""
        logger.info(f"Uploading results for job {job.job_id}")
        
        # Compress output directory
        import tarfile
        import os
        
        output_path = f'/tmp/node3_output/{job.job_id}_output.tar.gz'
        with tarfile.open(output_path, 'w:gz') as tar:
            tar.add('/tmp/node3_output/', arcname='output')
            
        # Upload to provided URL
        async with httpx.AsyncClient() as client:
            with open(output_path, 'rb') as f:
                response = await client.put(
                    job.output_upload_url,
                    content=f.read(),
                    timeout=300.0
                )
                
            if response.status_code in [200, 201]:
                logger.info(f"Results uploaded for job {job.job_id}")
            else:
                raise Exception(f"Failed to upload results: {response.status_code}")
                
    async def report_job_success(self, job: Job):
        """Report successful job completion to marketplace"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.marketplace_url}/api/jobs/{job.job_id}/complete",
                    json={
                        'status': 'completed',
                        'started_at': job.started_at.isoformat(),
                        'completed_at': job.completed_at.isoformat(),
                        'duration': (job.completed_at - job.started_at).total_seconds()
                    },
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Reported success for job {job.job_id}")
                else:
                    logger.warning(f"Failed to report success: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error reporting job success: {e}")
            
    async def report_job_failure(self, job: Job):
        """Report job failure to marketplace"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.marketplace_url}/api/jobs/{job.job_id}/fail",
                    json={
                        'status': 'failed',
                        'error_message': job.error_message,
                        'started_at': job.started_at.isoformat() if job.started_at else None,
                        'failed_at': job.completed_at.isoformat() if job.completed_at else None
                    },
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Reported failure for job {job.job_id}")
                else:
                    logger.warning(f"Failed to report failure: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error reporting job failure: {e}")
            
    def stop(self):
        """Stop the job manager"""
        self.is_running = False
        logger.info("Job manager stopped")
```

---

### 3. Docker Container Manager

**Purpose:** Execute jobs in isolated Docker containers with GPU access

**Features:**
- Pull Docker images
- Run containers with GPU access (nvidia-docker)
- Resource limits (GPU, CPU, RAM)
- Timeout handling
- Cleanup after execution

**Implementation:**

```python
# docker_manager.py

import docker
from typing import Dict, Optional, List
from loguru import logger
import asyncio

class DockerManager:
    """Manage Docker containers for job execution"""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized")
            
            # Test Docker connection
            self.client.ping()
            logger.info("Docker daemon is running")
            
            # Check for nvidia-docker runtime
            info = self.client.info()
            runtimes = info.get('Runtimes', {})
            
            if 'nvidia' in runtimes:
                self.gpu_runtime = 'nvidia'
                logger.info("NVIDIA Docker runtime detected")
            else:
                logger.warning("NVIDIA Docker runtime not found. GPU jobs may fail.")
                self.gpu_runtime = None
                
        except Exception as e:
            logger.error(f"Failed to initialize Docker: {e}")
            raise
            
    async def run_job(self,
                     image: str,
                     command: List[str],
                     environment: Dict[str, str],
                     gpu_id: int = 0,
                     timeout: int = 3600,
                     volumes: Optional[Dict] = None) -> Dict:
        """
        Run a job in a Docker container with GPU access
        
        Args:
            image: Docker image to use
            command: Command to run in container
            environment: Environment variables
            gpu_id: GPU device ID to use
            timeout: Maximum execution time in seconds
            volumes: Volume mounts
            
        Returns:
            Dict with 'success', 'output', 'error'
        """
        try:
            # Pull image if not exists
            await self.pull_image(image)
            
            # Configure device requests for GPU
            device_requests = []
            if self.gpu_runtime:
                device_requests = [
                    docker.types.DeviceRequest(
                        device_ids=[str(gpu_id)],
                        capabilities=[['gpu']]
                    )
                ]
                
            # Run container
            logger.info(f"Starting container: {image}")
            
            container = self.client.containers.run(
                image=image,
                command=command,
                environment=environment,
                device_requests=device_requests,
                volumes=volumes or {},
                detach=True,
                remove=False,  # Keep container for log inspection
                network_mode='none',  # Isolate from network for security
                mem_limit='8g',  # Limit RAM
                cpu_count=4,  # Limit CPU cores
            )
            
            # Wait for container with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(container.wait),
                    timeout=timeout
                )
                
                # Get logs
                logs = container.logs().decode('utf-8')
                
                # Check exit code
                exit_code = result['StatusCode']
                
                if exit_code == 0:
                    logger.info(f"Container completed successfully")
                    return {
                        'success': True,
                        'output': logs,
                        'exit_code': exit_code
                    }
                else:
                    logger.error(f"Container failed with exit code {exit_code}")
                    return {
                        'success': False,
                        'error': f"Exit code {exit_code}",
                        'output': logs
                    }
                    
            except asyncio.TimeoutError:
                logger.error(f"Container timeout after {timeout}s")
                container.stop(timeout=10)
                container.remove()
                return {
                    'success': False,
                    'error': f"Timeout after {timeout}s"
                }
                
            finally:
                # Cleanup
                try:
                    container.remove()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error running container: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def pull_image(self, image: str):
        """Pull Docker image if not exists"""
        try:
            # Check if image exists locally
            try:
                self.client.images.get(image)
                logger.info(f"Image {image} already exists locally")
                return
            except docker.errors.ImageNotFound:
                pass
                
            # Pull image
            logger.info(f"Pulling image: {image}")
            await asyncio.to_thread(self.client.images.pull, image)
            logger.info(f"Image {image} pulled successfully")
            
        except Exception as e:
            logger.error(f"Failed to pull image {image}: {e}")
            raise
            
    def list_images(self) -> List[str]:
        """List all local Docker images"""
        try:
            images = self.client.images.list()
            return [img.tags[0] if img.tags else img.id for img in images]
        except Exception as e:
            logger.error(f"Failed to list images: {e}")
            return []
            
    def cleanup_old_containers(self):
        """Remove old stopped containers"""
        try:
            filters = {'status': 'exited'}
            containers = self.client.containers.list(all=True, filters=filters)
            
            for container in containers:
                try:
                    container.remove()
                    logger.info(f"Removed old container: {container.id[:12]}")
                except Exception as e:
                    logger.warning(f"Failed to remove container {container.id[:12]}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup containers: {e}")
```

---

### 4. Payment Module (Solana)

**Purpose:** Handle wallet integration and payment receipt

**Features:**
- Generate or import Solana wallet
- Receive payments from marketplace
- Display balance
- Transaction history

**Implementation:**

```python
# payment_module.py

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.system_program import transfer, TransferParams
from solana.transaction import Transaction
from typing import Optional, List, Dict
from loguru import logger
import os
import json

class PaymentModule:
    """Handle Solana wallet and payments"""
    
    def __init__(self, 
                 rpc_url: str = "https://api.devnet.solana.com",
                 wallet_path: str = "./wallet.json"):
        self.rpc_url = rpc_url
        self.wallet_path = wallet_path
        self.client = AsyncClient(rpc_url)
        self.keypair: Optional[Keypair] = None
        self.pubkey: Optional[Pubkey] = None
        
    async def initialize(self):
        """Initialize or load wallet"""
        if os.path.exists(self.wallet_path):
            # Load existing wallet
            await self.load_wallet()
        else:
            # Create new wallet
            await self.create_wallet()
            
    async def create_wallet(self):
        """Create a new Solana wallet"""
        try:
            # Generate new keypair
            self.keypair = Keypair()
            self.pubkey = self.keypair.pubkey()
            
            # Save to file
            wallet_data = {
                'public_key': str(self.pubkey),
                'secret_key': list(bytes(self.keypair))
            }
            
            with open(self.wallet_path, 'w') as f:
                json.dump(wallet_data, f)
                
            logger.info(f"New wallet created: {self.pubkey}")
            logger.warning(f"IMPORTANT: Back up your wallet file: {self.wallet_path}")
            
        except Exception as e:
            logger.error(f"Failed to create wallet: {e}")
            raise
            
    async def load_wallet(self):
        """Load existing wallet from file"""
        try:
            with open(self.wallet_path, 'r') as f:
                wallet_data = json.load(f)
                
            # Recreate keypair from secret key
            secret_key_bytes = bytes(wallet_data['secret_key'])
            self.keypair = Keypair.from_bytes(secret_key_bytes)
            self.pubkey = self.keypair.pubkey()
            
            logger.info(f"Wallet loaded: {self.pubkey}")
            
        except Exception as e:
            logger.error(f"Failed to load wallet: {e}")
            raise
            
    async def get_balance(self) -> float:
        """Get wallet balance in SOL"""
        try:
            response = await self.client.get_balance(self.pubkey, commitment=Confirmed)
            balance_lamports = response.value
            balance_sol = balance_lamports / 1e9  # Convert lamports to SOL
            
            logger.info(f"Balance: {balance_sol} SOL")
            return balance_sol
            
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0
            
    async def get_recent_transactions(self, limit: int = 10) -> List[Dict]:
        """Get recent transactions for this wallet"""
        try:
            response = await self.client.get_signatures_for_address(
                self.pubkey,
                limit=limit
            )
            
            transactions = []
            for tx in response.value:
                transactions.append({
                    'signature': str(tx.signature),
                    'slot': tx.slot,
                    'block_time': tx.block_time,
                    'confirmation_status': tx.confirmation_status
                })
                
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get transactions: {e}")
            return []
            
    async def wait_for_payment(self, expected_amount: float, timeout: int = 300) -> bool:
        """
        Wait for an incoming payment
        
        Args:
            expected_amount: Expected payment amount in SOL
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if payment received, False otherwise
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        initial_balance = await self.get_balance()
        
        logger.info(f"Waiting for payment of {expected_amount} SOL...")
        
        while True:
            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > timeout:
                logger.warning(f"Payment timeout after {timeout}s")
                return False
                
            current_balance = await self.get_balance()
            
            if current_balance >= initial_balance + expected_amount:
                logger.info(f"Payment received: {current_balance - initial_balance} SOL")
                return True
                
            await asyncio.sleep(5)  # Check every 5 seconds
            
    def get_wallet_address(self) -> str:
        """Get wallet public address as string"""
        return str(self.pubkey)
        
    async def close(self):
        """Close the RPC client"""
        await self.client.close()
```

---

### 5. Local Dashboard (Web UI)

**Purpose:** Provide real-time monitoring and control interface

**Features:**
- Display GPU status and utilization
- Show active and completed jobs
- Real-time earnings tracking
- Wallet balance and transaction history
- Agent settings and configuration
- Start/stop controls

**Implementation:**

```python
# dashboard.py

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from typing import Dict, List
import json
from datetime import datetime
from loguru import logger

app = FastAPI(title="node3 Agent Dashboard")

# Mount static files and templates
# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class Dashboard:
    """Dashboard server for node3 agent"""
    
    def __init__(self, 
                 gpu_detector,
                 job_manager,
                 payment_module,
                 port: int = 8080):
        self.gpu_detector = gpu_detector
        self.job_manager = job_manager
        self.payment_module = payment_module
        self.port = port
        self.active_websockets: List[WebSocket] = []
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """Main dashboard page"""
            return templates.TemplateResponse("index.html", {
                "request": request
            })
            
        @app.get("/api/status")
        async def get_status():
            """Get current agent status"""
            gpus = self.gpu_detector.gpus
            
            gpu_data = []
            for gpu in gpus:
                util = self.gpu_detector.get_gpu_utilization(gpu.index)
                gpu_data.append({
                    'index': gpu.index,
                    'name': gpu.name,
                    'memory': gpu.total_memory,
                    'utilization': util.get('gpu_utilization', 0),
                    'memory_used': util.get('memory_used', 0),
                    'temperature': util.get('temperature', 0),
                    'power': util.get('power_usage', 0)
                })
                
            return {
                'gpus': gpu_data,
                'active_jobs': len(self.job_manager.active_jobs),
                'completed_jobs': len(self.job_manager.job_history),
                'wallet_address': self.payment_module.get_wallet_address(),
                'balance': await self.payment_module.get_balance(),
                'status': 'running' if self.job_manager.is_running else 'stopped'
            }
            
        @app.get("/api/jobs")
        async def get_jobs():
            """Get job history"""
            jobs = []
            
            for job in self.job_manager.job_history[-50:]:  # Last 50 jobs
                jobs.append({
                    'job_id': job.job_id,
                    'job_type': job.job_type,
                    'status': job.status.value,
                    'reward': job.reward,
                    'duration': (job.completed_at - job.started_at).total_seconds() if job.completed_at and job.started_at else None,
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None
                })
                
            return {'jobs': jobs}
            
        @app.get("/api/earnings")
        async def get_earnings():
            """Get earnings statistics"""
            total_earnings = sum(job.reward for job in self.job_manager.job_history if job.status.value == 'completed')
            
            today_earnings = sum(
                job.reward for job in self.job_manager.job_history 
                if job.status.value == 'completed' and 
                job.completed_at and 
                job.completed_at.date() == datetime.now().date()
            )
            
            return {
                'total_earnings': total_earnings,
                'today_earnings': today_earnings,
                'completed_jobs': len([j for j in self.job_manager.job_history if j.status.value == 'completed']),
                'failed_jobs': len([j for j in self.job_manager.job_history if j.status.value == 'failed'])
            }
            
        @app.post("/api/start")
        async def start_agent():
            """Start the agent"""
            if not self.job_manager.is_running:
                import asyncio
                asyncio.create_task(self.job_manager.start())
                return {'status': 'started'}
            return {'status': 'already_running'}
            
        @app.post("/api/stop")
        async def stop_agent():
            """Stop the agent"""
            self.job_manager.stop()
            return {'status': 'stopped'}
            
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates"""
            await websocket.accept()
            self.active_websockets.append(websocket)
            
            try:
                while True:
                    # Send status updates every 2 seconds
                    import asyncio
                    await asyncio.sleep(2)
                    
                    status = await get_status()
                    await websocket.send_json(status)
                    
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self.active_websockets.remove(websocket)
                
    async def start(self):
        """Start the dashboard server"""
        self.setup_routes()
        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
```

**HTML Template (`templates/index.html`):**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>node3 Agent Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            margin-bottom: 40px;
        }
        
        h1 {
            font-size: 32px;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #2a2a2a;
        }
        
        .card h2 {
            font-size: 18px;
            margin-bottom: 16px;
            color: #888;
        }
        
        .stat {
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .label {
            color: #666;
            font-size: 14px;
        }
        
        .gpu-list {
            margin-top: 20px;
        }
        
        .gpu-item {
            background: #0f0f0f;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 12px;
        }
        
        .gpu-name {
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .gpu-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            font-size: 14px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-running {
            background: #10b981;
        }
        
        .status-stopped {
            background: #ef4444;
        }
        
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        
        .button:hover {
            transform: translateY(-2px);
        }
        
        .button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .controls {
            display: flex;
            gap: 12px;
            margin-top: 20px;
        }
        
        .jobs-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }
        
        .jobs-table th,
        .jobs-table td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #2a2a2a;
        }
        
        .jobs-table th {
            color: #888;
            font-weight: 600;
            font-size: 14px;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .badge-completed {
            background: #10b98120;
            color: #10b981;
        }
        
        .badge-failed {
            background: #ef444420;
            color: #ef4444;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>node³ Agent</h1>
            <p style="color: #666;">Turn Your GPU Into Passive Income</p>
        </header>
        
        <div class="grid">
            <div class="card">
                <h2>WALLET BALANCE</h2>
                <div class="stat" id="balance">0.00 SOL</div>
                <div class="label" id="wallet-address">Loading...</div>
            </div>
            
            <div class="card">
                <h2>TODAY'S EARNINGS</h2>
                <div class="stat" id="today-earnings">0.00 SOL</div>
                <div class="label">Total: <span id="total-earnings">0.00 SOL</span></div>
            </div>
            
            <div class="card">
                <h2>JOBS COMPLETED</h2>
                <div class="stat" id="completed-jobs">0</div>
                <div class="label"><span id="active-jobs">0</span> active</div>
            </div>
            
            <div class="card">
                <h2>STATUS</h2>
                <div>
                    <span class="status-indicator status-running" id="status-indicator"></span>
                    <span id="status-text">Running</span>
                </div>
                <div class="controls">
                    <button class="button" onclick="startAgent()" id="start-btn">Start</button>
                    <button class="button" onclick="stopAgent()" id="stop-btn">Stop</button>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>GPU INFORMATION</h2>
            <div class="gpu-list" id="gpu-list">
                Loading...
            </div>
        </div>
        
        <div class="card">
            <h2>RECENT JOBS</h2>
            <table class="jobs-table" id="jobs-table">
                <thead>
                    <tr>
                        <th>Job ID</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Reward</th>
                        <th>Duration</th>
                        <th>Completed</th>
                    </tr>
                </thead>
                <tbody id="jobs-tbody">
                    <tr>
                        <td colspan="6" style="text-align: center; color: #666;">No jobs yet</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        let ws;
        
        function connectWebSocket() {
            ws = new WebSocket('ws://127.0.0.1:8080/ws');
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onclose = function() {
                setTimeout(connectWebSocket, 3000);
            };
        }
        
        function updateDashboard(data) {
            // Update balance and earnings
            document.getElementById('balance').textContent = data.balance.toFixed(4) + ' SOL';
            document.getElementById('wallet-address').textContent = data.wallet_address;
            
            // Update status
            const statusIndicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');
            
            if (data.status === 'running') {
                statusIndicator.className = 'status-indicator status-running';
                statusText.textContent = 'Running';
            } else {
                statusIndicator.className = 'status-indicator status-stopped';
                statusText.textContent = 'Stopped';
            }
            
            // Update jobs
            document.getElementById('active-jobs').textContent = data.active_jobs;
            document.getElementById('completed-jobs').textContent = data.completed_jobs;
            
            // Update GPU list
            const gpuList = document.getElementById('gpu-list');
            gpuList.innerHTML = data.gpus.map(gpu => `
                <div class="gpu-item">
                    <div class="gpu-name">${gpu.name}</div>
                    <div class="gpu-stats">
                        <div>Utilization: ${gpu.utilization}%</div>
                        <div>Temperature: ${gpu.temperature}°C</div>
                        <div>Memory: ${(gpu.memory_used / 1e9).toFixed(1)}GB / ${(gpu.memory / 1e9).toFixed(1)}GB</div>
                        <div>Power: ${gpu.power.toFixed(0)}W</div>
                    </div>
                </div>
            `).join('');
        }
        
        async function fetchEarnings() {
            const response = await fetch('/api/earnings');
            const data = await response.json();
            
            document.getElementById('today-earnings').textContent = data.today_earnings.toFixed(4) + ' SOL';
            document.getElementById('total-earnings').textContent = data.total_earnings.toFixed(4) + ' SOL';
        }
        
        async function fetchJobs() {
            const response = await fetch('/api/jobs');
            const data = await response.json();
            
            const tbody = document.getElementById('jobs-tbody');
            
            if (data.jobs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #666;">No jobs yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = data.jobs.reverse().map(job => `
                <tr>
                    <td>${job.job_id.substring(0, 8)}...</td>
                    <td>${job.job_type}</td>
                    <td><span class="badge badge-${job.status}">${job.status}</span></td>
                    <td>${job.reward.toFixed(4)} SOL</td>
                    <td>${job.duration ? job.duration.toFixed(0) + 's' : 'N/A'}</td>
                    <td>${job.completed_at ? new Date(job.completed_at).toLocaleString() : 'N/A'}</td>
                </tr>
            `).join('');
        }
        
        async function startAgent() {
            await fetch('/api/start', { method: 'POST' });
        }
        
        async function stopAgent() {
            await fetch('/api/stop', { method: 'POST' });
        }
        
        // Initialize
        connectWebSocket();
        setInterval(fetchEarnings, 5000);
        setInterval(fetchJobs, 10000);
        fetchEarnings();
        fetchJobs();
    </script>
</body>
</html>
```

---

### 6. Main Application Entry Point

**Purpose:** Orchestrate all modules and run the agent

**Implementation:**

```python
# main.py

import asyncio
from loguru import logger
import sys
from pathlib import Path

# Import modules
from gpu_detector import GPUDetector
from docker_manager import DockerManager
from job_manager import JobManager
from payment_module import PaymentModule
from dashboard import Dashboard

# Configuration
MARKETPLACE_URL = "https://api.node-3.com"  # TODO: Replace with actual URL
API_KEY = ""  # TODO: Load from config
WALLET_PATH = "./wallet.json"

async def main():
    """Main application entry point"""
    
    logger.info("Starting node3 Agent...")
    
    try:
        # 1. Initialize GPU Detector
        logger.info("Initializing GPU detector...")
        gpu_detector = GPUDetector()
        gpus = gpu_detector.detect_gpus()
        
        if not gpus:
            logger.error("No GPUs detected. Exiting.")
            sys.exit(1)
            
        # Benchmark GPUs
        for gpu in gpus:
            logger.info(f"Benchmarking {gpu.name}...")
            benchmark = gpu_detector.benchmark_gpu(gpu.index)
            logger.info(f"Performance: {benchmark.get('tflops', 0):.2f} TFLOPS")
            
        # 2. Initialize Docker Manager
        logger.info("Initializing Docker manager...")
        docker_manager = DockerManager()
        
        # 3. Initialize Payment Module
        logger.info("Initializing payment module...")
        payment_module = PaymentModule(wallet_path=WALLET_PATH)
        await payment_module.initialize()
        
        wallet_address = payment_module.get_wallet_address()
        balance = await payment_module.get_balance()
        
        logger.info(f"Wallet: {wallet_address}")
        logger.info(f"Balance: {balance} SOL")
        
        # 4. Initialize Job Manager
        logger.info("Initializing job manager...")
        job_manager = JobManager(
            marketplace_url=MARKETPLACE_URL,
            api_key=API_KEY,
            gpu_info={
                'name': gpus[0].name,
                'total_memory': gpus[0].total_memory,
                'compute_capability': gpus[0].compute_capability
            },
            docker_manager=docker_manager
        )
        
        # 5. Start Dashboard
        logger.info("Starting dashboard...")
        dashboard = Dashboard(
            gpu_detector=gpu_detector,
            job_manager=job_manager,
            payment_module=payment_module,
            port=8080
        )
        
        # 6. Start all services
        logger.info("node3 Agent started successfully!")
        logger.info("Dashboard available at: http://127.0.0.1:8080")
        
        # Run job manager and dashboard concurrently
        await asyncio.gather(
            job_manager.start(),
            dashboard.start()
        )
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'payment_module' in locals():
            await payment_module.close()
        if 'gpu_detector' in locals():
            gpu_detector.shutdown()
            
if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/node3_agent_{time}.log",
        rotation="100 MB",
        retention="10 days",
        level="DEBUG"
    )
    
    # Run
    asyncio.run(main())
```

---

## Installation & Setup Instructions

### Prerequisites

```bash
# System requirements
- Python 3.10+
- NVIDIA GPU with CUDA support
- Docker with nvidia-docker runtime
- 8GB+ RAM
- 50GB+ disk space

# Install CUDA drivers (if not installed)
# Visit: https://developer.nvidia.com/cuda-downloads

# Install Docker
# Visit: https://docs.docker.com/get-docker/

# Install nvidia-docker
# Visit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/node3/agent.git
cd agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure agent
cp .env.example .env
# Edit .env with your configuration

# 5. Run agent
python main.py
```

### Requirements.txt

```txt
# GPU Management
pynvml==11.5.0
py3nvml==0.2.7
torch==2.1.0

# Container Management
docker==6.1.3

# HTTP & WebSocket
httpx==0.25.0
aiohttp==3.9.0
websockets==12.0

# Blockchain
solana==0.30.2
solders==0.18.0

# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
jinja2==3.1.2

# Utilities
pydantic==2.5.0
python-dotenv==1.0.0
psutil==5.9.6
loguru==0.7.2
```

### Environment Variables (.env.example)

```bash
# Marketplace Configuration
MARKETPLACE_URL=https://api.node-3.com
API_KEY=your_api_key_here

# Wallet Configuration
WALLET_PATH=./wallet.json
SOLANA_RPC_URL=https://api.devnet.solana.com

# Agent Configuration
DASHBOARD_PORT=8080
GPU_INDEX=0
MAX_CONCURRENT_JOBS=1
LOG_LEVEL=INFO

# Docker Configuration
DOCKER_NETWORK=none
MEMORY_LIMIT=8g
CPU_LIMIT=4
```

---

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
├── README.md              # Setup and usage instructions
├── templates/
│   └── index.html         # Dashboard HTML template
├── logs/                  # Log files
└── wallet.json            # Solana wallet (gitignored)
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_gpu_detector.py
import pytest
from gpu_detector import GPUDetector

def test_gpu_detection():
    detector = GPUDetector()
    gpus = detector.detect_gpus()
    assert len(gpus) > 0
    
def test_gpu_utilization():
    detector = GPUDetector()
    detector.detect_gpus()
    util = detector.get_gpu_utilization(0)
    assert 'gpu_utilization' in util
    assert 0 <= util['gpu_utilization'] <= 100
```

### Integration Tests

```python
# tests/test_job_execution.py
import pytest
from docker_manager import DockerManager

@pytest.mark.asyncio
async def test_simple_job():
    manager = DockerManager()
    
    result = await manager.run_job(
        image='nvidia/cuda:11.8.0-base-ubuntu22.04',
        command=['nvidia-smi'],
        environment={},
        gpu_id=0,
        timeout=60
    )
    
    assert result['success'] == True
    assert 'NVIDIA' in result['output']
```

### Manual Testing Checklist

- [ ] Agent detects GPUs correctly
- [ ] Benchmark runs successfully
- [ ] Dashboard loads at localhost:8080
- [ ] Wallet created and displays address
- [ ] Docker containers can run with GPU access
- [ ] Job manager connects to marketplace
- [ ] Jobs execute and complete
- [ ] Payments received correctly
- [ ] Agent handles errors gracefully
- [ ] Agent can stop/start cleanly

---

## Security Considerations

### Container Isolation
- Jobs run in isolated Docker containers
- No network access (`network_mode='none'`)
- Resource limits enforced (RAM, CPU, GPU)
- Containers removed after execution

### Wallet Security
- Wallet stored locally, encrypted
- Private keys never leave user's machine
- Backup wallet file prominently warned
- Support hardware wallets (future)

### API Security
- HTTPS only for marketplace communication
- API key authentication
- Rate limiting on agent endpoints
- Input validation on all user inputs

### Code Execution
- Only trusted Docker images allowed
- Image verification via checksums
- Sandboxed execution environment
- Monitor for suspicious activity

---

## Performance Optimization

### GPU Utilization
- Monitor GPU usage to avoid conflicts with user
- Only accept jobs when GPU is idle (< 20% utilization)
- Prioritize jobs that fully utilize GPU
- Batch multiple small jobs when possible

### Network Efficiency
- Compress data transfers
- Use persistent connections
- Cache Docker images locally
- Resume interrupted downloads

### Resource Management
- Cleanup old containers regularly
- Manage disk space for job data
- Monitor system resources
- Graceful degradation under load

---

## Deployment

### Packaging (PyInstaller)

```bash
# Build executable
pyinstaller --onefile --windowed main.py

# Package for distribution
# Windows: Create .exe installer
# Mac: Create .dmg
# Linux: Create .deb/.rpm
```

### Auto-Start Configuration

**Windows:**
```bash
# Create Windows service or add to startup folder
```

**Mac:**
```bash
# Create launchd service
# ~/Library/LaunchAgents/com.node3.agent.plist
```

**Linux:**
```bash
# Create systemd service
# /etc/systemd/system/node3-agent.service
```

---

## Monitoring & Logging

### Log Levels
- INFO: Normal operations
- WARNING: Potential issues
- ERROR: Failures that don't crash agent
- DEBUG: Detailed debugging info

### Metrics to Track
- GPU utilization over time
- Jobs completed vs. failed
- Average job duration
- Earnings per hour/day
- Network bandwidth usage
- System resource usage

### Health Checks
- GPU availability
- Docker daemon status
- Marketplace connectivity
- Wallet balance updates
- Disk space availability

---

## Roadmap

### Phase 1 (MVP) - Weeks 1-4
- ✓ GPU detection
- ✓ Job execution in Docker
- ✓ Basic marketplace integration
- ✓ Wallet and payments
- ✓ Simple dashboard

### Phase 2 (Beta) - Weeks 5-8
- Multi-GPU support
- AMD GPU support
- Advanced job scheduling
- Performance optimizations
- Enhanced dashboard
- Mobile monitoring app

### Phase 3 (Production) - Weeks 9-12
- CPU compute support
- Storage marketplace
- Bandwidth services
- Auto-updates
- Hardware wallet support
- Enterprise features

---

## Support & Documentation

### User Documentation
- Installation guide
- Troubleshooting FAQ
- Video tutorials
- Community forum

### Developer Documentation
- API reference
- Architecture diagrams
- Contributing guide
- Code style guide

---

## Conclusion

This specification provides everything needed to build the node3 Agent MVP. The architecture is modular, allowing for iterative development and testing.

**Next Steps:**
1. Set up development environment
2. Implement GPU detector module
3. Build Docker manager
4. Create job manager
5. Integrate Solana payments
6. Develop dashboard
7. Test end-to-end
8. Deploy to beta users

**Success Criteria:**
- Agent runs on Windows, Mac, Linux
- Successfully executes GPU compute jobs
- Payments work via Solana
- Dashboard provides real-time monitoring
- Ready for 100-500 beta testers

Let's build the people's cloud! 🚀
