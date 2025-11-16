# job_manager.py

import asyncio
import httpx
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
from pathlib import Path

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
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class JobManager:
    """Manage job lifecycle from marketplace to execution"""
    
    def __init__(self, 
                 marketplace_url: str,
                 api_key: str,
                 gpu_info: Dict,
                 docker_manager,
                 use_native_execution: bool = True,
                 payment_module = None,
                 telemetry = None):
        self.marketplace_url = marketplace_url
        self.api_key = api_key
        self.gpu_info = gpu_info
        self.docker_manager = docker_manager
        self.use_native_execution = use_native_execution
        self.payment_module = payment_module  # For wallet address
        self.telemetry = telemetry  # For telemetry reporting
        self.active_jobs: List[Job] = []
        self.job_history: List[Job] = []
        self.is_running = False
        self.total_jobs_completed = 0
        self.total_earnings = 0.0
        
        # Initialize native executor as fallback
        if use_native_execution:
            try:
                from native_executor import NativeExecutor
                self.native_executor = NativeExecutor()
                logger.info("Native executor initialized (fallback for jobs without containers)")
            except ImportError:
                logger.warning("Native executor not available - install psutil for native execution")
                self.native_executor = None
        else:
            self.native_executor = None
        
        # If docker_manager is None, disable container execution but allow native
        if docker_manager is None:
            if self.native_executor:
                logger.info("Job manager initialized without Docker - will use native execution")
            else:
                logger.warning("Job manager initialized without Docker - job execution disabled")
        
    async def start(self):
        """Start the job manager loop"""
        self.is_running = True
        logger.info("Job manager started")
        
        heartbeat_counter = 0
        
        while self.is_running:
            try:
                # Send heartbeat every 30 seconds (3 poll cycles)
                if heartbeat_counter >= 3:
                    await self.send_heartbeat()
                    heartbeat_counter = 0
                else:
                    heartbeat_counter += 1
                
                # Poll for new jobs
                await self.poll_marketplace()
                
                # Process queued jobs
                await self.process_jobs()
                
                # Wait before next poll
                await asyncio.sleep(10)  # Poll every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in job manager loop: {e}")
                await asyncio.sleep(30)
                
    async def send_heartbeat(self):
        """Send heartbeat to marketplace and telemetry server"""
        # Send to marketplace
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.marketplace_url}/api/agents/heartbeat",
                    headers={'X-API-Key': self.api_key} if self.api_key else {},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    logger.debug("Heartbeat sent successfully")
                else:
                    logger.warning(f"Heartbeat failed: {response.status_code}")
                    
        except Exception as e:
            logger.debug(f"Error sending heartbeat: {e}")
        
        # Send to telemetry server
        if self.telemetry:
            try:
                status = 'working' if len(self.active_jobs) > 0 else 'online'
                self.telemetry.send_heartbeat(
                    status=status,
                    total_jobs=self.total_jobs_completed,
                    total_earnings=self.total_earnings
                )
            except Exception as e:
                logger.debug(f"Error sending telemetry heartbeat: {e}")
    
    async def poll_marketplace(self):
        """Poll marketplace for available jobs
        
        Returns:
            List[Job]: List of jobs that were accepted
        """
        accepted_jobs = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.marketplace_url}/api/jobs/available",
                    json={
                        'gpu_model': self.gpu_info['name'],
                        'gpu_vendor': self.gpu_info.get('vendor', 'unknown'),
                        'gpu_type': self.gpu_info.get('gpu_type', 'unknown'),
                        'compute_framework': self.gpu_info.get('compute_framework', 'none'),
                        'gpu_memory': self.gpu_info['total_memory'],
                        'compute_capability': self.gpu_info.get('compute_capability'),
                        'max_concurrent_jobs': 1  # MVP: one job at a time
                    },
                    headers={'X-API-Key': self.api_key} if self.api_key else {},
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
                        accepted_jobs.append(job)
                        
                else:
                    logger.warning(f"Failed to poll marketplace: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error polling marketplace: {e}")
        
        return accepted_jobs
    
    async def accept_job(self, job: Job):
        """Accept a job from the marketplace - includes wallet address for payment"""
        try:
            # Get wallet address for payment
            wallet_address = None
            if self.payment_module:
                wallet_address = self.payment_module.get_wallet_address()
            
            if not wallet_address:
                logger.error("Cannot accept job: No wallet address available")
                return
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.marketplace_url}/api/jobs/{job.job_id}/accept",
                    headers={'X-API-Key': self.api_key} if self.api_key else {},
                    json={"wallet_address": wallet_address},  # Send wallet for payment
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.active_jobs.append(job)
                    logger.info(f"Accepted job {job.job_id}: {job.job_type} - {job.reward} SOL")
                    logger.info(f"Payment will be sent to: {wallet_address}")
                else:
                    logger.warning(f"Failed to accept job {job.job_id}: {response.status_code}")
                    if response.status_code == 400:
                        logger.error(f"Error: {response.text}")
                    
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
        """Execute a job - uses native execution by default, Docker/Lima if available and preferred"""
        # Native execution is the default - works out of the box
        # Docker/Lima is optional enhancement for better isolation
        
        # Check if job requires container (specified in job metadata)
        job_requires_container = job.environment.get('REQUIRE_CONTAINER', 'false').lower() == 'true'
        
        # Determine execution method (native first, containers optional)
        use_container = False
        if job_requires_container:
            # Job explicitly requires container
            use_container = (self.docker_manager is not None and 
                            self.docker_manager.is_available())
            if not use_container:
                logger.warning(f"Job {job.job_id} requires container but none available - will attempt native execution")
        
        # Use native execution by default
        if not use_container and self.native_executor:
            executor_type = "native"
        elif use_container:
            executor_type = "container"
        else:
            logger.error("Cannot execute job - Native executor not available")
            job.status = JobStatus.FAILED
            job.error_message = "Job execution not available"
            job.completed_at = datetime.now()
            await self.report_job_failure(job)
            return
            
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            
            logger.info(f"Executing job {job.job_id} using {executor_type} execution")
            
            # Download input data
            await self.download_input_data(job)
            
            # Execute based on method
            if executor_type == "container":
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
            else:
                # Run natively
                input_dir = Path('/tmp/node3_input')
                output_dir = Path('/tmp/node3_output')
                
                result = await self.native_executor.run_job(
                    job_id=job.job_id,
                    command=job.command,
                    environment=job.environment,
                    timeout=job.timeout,
                    input_dir=input_dir,
                    output_dir=output_dir
                )
            
            if result['success']:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                
                # Upload results
                await self.upload_results(job)
                
                # Report success
                await self.report_job_success(job)
                
                # Update telemetry stats
                self.total_jobs_completed += 1
                self.total_earnings += job.reward
                
                # Log telemetry event
                if self.telemetry:
                    try:
                        self.telemetry.log_event('job_completed', {
                            'job_id': job.job_id,
                            'job_type': job.job_type,
                            'reward': job.reward,
                            'duration': (job.completed_at - job.started_at).total_seconds() if job.started_at else 0
                        })
                    except Exception as e:
                        logger.debug(f"Error logging telemetry event: {e}")
                
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
            
            # Log telemetry event for failure
            if self.telemetry:
                try:
                    self.telemetry.log_event('job_failed', {
                        'job_id': job.job_id,
                        'job_type': job.job_type,
                        'error': str(e)
                    })
                except Exception as telemetry_error:
                    logger.debug(f"Error logging telemetry event: {telemetry_error}")
            
            # Remove job from active list first to prevent it from being stuck
            # even if report_job_failure fails
            try:
                if job in self.active_jobs:
                    self.active_jobs.remove(job)
                self.job_history.append(job)
            except Exception as cleanup_error:
                logger.error(f"Error removing job from active list: {cleanup_error}")
            
            # Report failure after cleanup to ensure job is removed even if report fails
            try:
                await self.report_job_failure(job)
            except Exception as report_error:
                logger.error(f"Failed to report job failure: {report_error}")
            
    async def download_input_data(self, job: Job):
        """Download input data for job (optional if URL is empty)"""
        # Skip if no input URL provided (test jobs may not need input)
        if not job.input_data_url or not job.input_data_url.strip():
            logger.info(f"No input data URL for job {job.job_id} - skipping download")
            # Ensure input directory exists anyway
            import os
            os.makedirs('/tmp/node3_input', exist_ok=True)
            return
        
        # Validate URL has protocol
        if not job.input_data_url.startswith(('http://', 'https://')):
            logger.warning(f"Invalid input_data_url for job {job.job_id}: {job.input_data_url}")
            logger.info("Skipping input download - job will run without input data")
            import os
            os.makedirs('/tmp/node3_input', exist_ok=True)
            return
        
        logger.info(f"Downloading input data for job {job.job_id}")
        
        try:
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
                    logger.warning(f"Failed to download input data: {response.status_code} - continuing without input")
                    import os
                    os.makedirs('/tmp/node3_input', exist_ok=True)
        except Exception as e:
            logger.warning(f"Error downloading input data: {e} - continuing without input")
            import os
            os.makedirs('/tmp/node3_input', exist_ok=True)
                
    async def upload_results(self, job: Job):
        """Upload job results (optional if URL is empty)"""
        # Skip if no upload URL provided (test jobs may not need upload)
        if not job.output_upload_url or not job.output_upload_url.strip():
            logger.info(f"No output upload URL for job {job.job_id} - skipping upload")
            logger.info(f"Results are available locally at /tmp/node3_output/")
            return
        
        # Validate URL has protocol
        if not job.output_upload_url.startswith(('http://', 'https://')):
            logger.warning(f"Invalid output_upload_url for job {job.job_id}: {job.output_upload_url}")
            logger.info("Skipping result upload - results available locally at /tmp/node3_output/")
            return
        
        logger.info(f"Uploading results for job {job.job_id}")
        
        try:
            # Compress output directory
            import tarfile
            import os
            
            output_path = f'/tmp/node3_output/{job.job_id}_output.tar.gz'
            os.makedirs('/tmp/node3_output', exist_ok=True)
            
            # Check if output directory has any files
            output_files = list(Path('/tmp/node3_output').glob('*'))
            if not output_files:
                logger.info("No output files to upload")
                return
            
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
                    logger.warning(f"Failed to upload results: {response.status_code} - results saved locally")
        except Exception as e:
            logger.warning(f"Error uploading results: {e} - results saved locally at /tmp/node3_output/")
                
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
                    headers={'X-API-Key': self.api_key} if self.api_key else {},
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
                    headers={'X-API-Key': self.api_key} if self.api_key else {},
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

