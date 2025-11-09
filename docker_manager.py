# docker_manager.py

import docker
from typing import Dict, Optional, List
from loguru import logger
import asyncio
import subprocess
import shutil
import os
import sys
from pathlib import Path
from gpu_detector import GPUType, ComputeFramework

class DockerManager:
    """Manage Docker containers for job execution with multi-GPU support
    
    Supports Docker Desktop and Lima (lightweight Docker alternative)
    """
    
    def __init__(self, gpu_info: Optional[Dict] = None):
        self.client = None
        self.gpu_runtime = None
        self.gpu_type = None
        self.compute_framework = None
        self.runtime_type = None  # 'docker' or 'lima'
        
        # Store GPU info if provided
        if gpu_info:
            self.gpu_type = GPUType(gpu_info.get('gpu_type', 'unknown'))
            self.compute_framework = ComputeFramework(gpu_info.get('compute_framework', 'none'))
        
        # Try Docker first, then Lima
        if self._try_docker():
            logger.info("Using Docker runtime")
            self.runtime_type = 'docker'
        elif self._try_lima():
            logger.info("Using Lima runtime")
            self.runtime_type = 'lima'
        else:
            logger.warning("No container runtime available. Job execution will be disabled.")
            logger.warning("Dashboard and wallet features will still work.")
            self.gpu_runtime = None
            self.gpu_type = None
            self.compute_framework = None
    
    def _try_docker(self) -> bool:
        """Try to initialize Docker client"""
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized")
            
            # Test Docker connection
            self.client.ping()
            logger.info("Docker daemon is running")
            
            # Check for GPU runtimes
            info = self.client.info()
            runtimes = info.get('Runtimes', {})
            
            # Detect available GPU runtimes
            if 'nvidia' in runtimes:
                self.gpu_runtime = 'nvidia'
                logger.info("NVIDIA Docker runtime detected")
            elif 'rocm' in runtimes:
                self.gpu_runtime = 'rocm'
                logger.info("ROCm Docker runtime detected")
            else:
                logger.warning("No GPU Docker runtime detected. GPU jobs may run without GPU acceleration.")
            
            return True
            
        except Exception as e:
            logger.debug(f"Docker not available: {e}")
            self.client = None
            return False
    
    def _try_lima(self) -> bool:
        """Try to initialize Lima runtime"""
        try:
            # Check if Lima is installed
            lima_path = shutil.which('lima')
            if not lima_path:
                logger.debug("Lima not found in PATH")
                # Try to find bundled Lima binary
                # Check in app bundle Resources (for DMG distribution)
                if getattr(sys, 'frozen', False):
                    # Running from PyInstaller bundle
                    app_dir = Path(sys.executable).parent.parent.parent  # MacOS -> Contents -> app bundle
                    bundled_lima = app_dir / 'Resources' / 'lima' / 'bin' / 'lima'
                else:
                    # Running from source
                    app_dir = Path(__file__).parent.parent
                    bundled_lima = app_dir / 'lima' / 'bin' / 'lima'
                
                if bundled_lima.exists():
                    lima_path = str(bundled_lima)
                    logger.info(f"Using bundled Lima: {lima_path}")
                    # Set LIMACTL to point to bundled limactl
                    limactl_path = bundled_lima.parent / 'limactl'
                    if limactl_path.exists():
                        os.environ['LIMACTL'] = str(limactl_path)
                        logger.debug(f"Set LIMACTL={limactl_path}")
                else:
                    logger.debug(f"Bundled Lima not found at {bundled_lima}")
                    return False
            
            # Check if Lima instance exists
            lima_instance = 'node3-agent'
            result = subprocess.run(
                [lima_path, 'list', lima_instance],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Create Lima instance if it doesn't exist
            if result.returncode != 0 or lima_instance not in result.stdout:
                logger.info(f"Setting up Lima instance '{lima_instance}'...")
                if not self._setup_lima_instance(lima_path, lima_instance):
                    return False
            
            # Start Lima instance if not running
            subprocess.run(
                [lima_path, 'start', lima_instance],
                capture_output=True,
                timeout=30
            )
            
            # Set DOCKER_HOST to use Lima's Docker socket
            docker_socket = f"unix://{Path.home()}/.lima/{lima_instance}/sock/docker.sock"
            os.environ['DOCKER_HOST'] = docker_socket
            
            # Try to connect to Docker via Lima
            try:
                self.client = docker.from_env()
                self.client.ping()
                logger.info(f"Lima Docker daemon is running (instance: {lima_instance})")
                
                # Check for GPU runtimes (Lima supports GPU passthrough on macOS)
                info = self.client.info()
                runtimes = info.get('Runtimes', {})
                
                if 'nvidia' in runtimes:
                    self.gpu_runtime = 'nvidia'
                    logger.info("NVIDIA runtime detected via Lima")
                elif 'rocm' in runtimes:
                    self.gpu_runtime = 'rocm'
                    logger.info("ROCm runtime detected via Lima")
                else:
                    # On macOS, Metal/GPU access works natively through Lima
                    logger.info("Lima ready - GPU access depends on container configuration")
                
                return True
            except Exception as e:
                logger.debug(f"Failed to connect to Lima Docker socket: {e}")
                return False
                
        except Exception as e:
            logger.debug(f"Lima not available: {e}")
            return False
    
    def _setup_lima_instance(self, lima_path: str, instance_name: str) -> bool:
        """Setup Lima instance for node3 agent"""
        try:
            # Create Lima configuration
            lima_config = f"""
# Lima configuration for node3-agent
images:
  - location: "https://cloud-images.ubuntu.com/releases/22.04/release/ubuntu-22.04-server-cloudimg-amd64.img"
    arch: "x86_64"
cpus: 4
memory: "8GiB"
disk: "50GiB"
mounts:
  - location: "~"
    writable: true
provision:
  - mode: system
    script: |
      #!/bin/bash
      set -eux -o pipefail
      export DEBIAN_FRONTEND=noninteractive
      apt-get update
      apt-get install -y docker.io
      systemctl enable docker
      systemctl start docker
      usermod -aG docker $USER
networks:
  - lima
"""
            
            # Write config to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(lima_config)
                config_path = f.name
            
            try:
                # Create Lima instance
                result = subprocess.run(
                    [lima_path, 'start', instance_name, '--config', config_path],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    logger.info(f"Lima instance '{instance_name}' created successfully")
                    return True
                else:
                    logger.error(f"Failed to create Lima instance: {result.stderr}")
                    return False
            finally:
                # Clean up temp config file
                try:
                    os.unlink(config_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Failed to setup Lima instance: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if container runtime is available"""
        return self.client is not None
    
    def _get_runtime_config(self, gpu_id: int = 0) -> Dict:
        """Get Docker runtime configuration based on GPU type"""
        config = {}
        
        if self.gpu_runtime == 'nvidia':
            config['runtime'] = 'nvidia'
            config['device_requests'] = [
                docker.types.DeviceRequest(
                    device_ids=[str(gpu_id)],
                    capabilities=[['gpu']]
                )
            ]
            config['environment'] = {
                'NVIDIA_VISIBLE_DEVICES': str(gpu_id)
            }
        elif self.gpu_runtime == 'rocm':
            config['runtime'] = 'rocm'
            config['device_requests'] = [
                docker.types.DeviceRequest(
                    device_ids=[str(gpu_id)],
                    capabilities=[['gpu']]
                )
            ]
            config['environment'] = {
                'HIP_VISIBLE_DEVICES': str(gpu_id)
            }
        else:
            # No GPU runtime - container will run without GPU
            # For Apple Silicon, Metal would work natively on macOS
            # For Intel, would need OpenCL containers
            config['runtime'] = None
            config['device_requests'] = []
            config['environment'] = {}
            
        return config
            
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
        if not self.client:
            return {
                'success': False,
                'error': 'Container runtime not available'
            }
        
        try:
            # Pull image if not exists
            await self.pull_image(image)
            
            # Get runtime configuration
            runtime_config = self._get_runtime_config(gpu_id)
            
            # Merge environment variables
            merged_env = {**runtime_config.get('environment', {}), **environment}
            
            # Run container
            logger.info(f"Starting container: {image}")
            if runtime_config.get('runtime'):
                logger.info(f"Using GPU runtime: {runtime_config['runtime']}")
            
            container = self.client.containers.run(
                image=image,
                command=command,
                environment=merged_env,
                device_requests=runtime_config.get('device_requests', []),
                volumes=volumes or {},
                detach=True,
                remove=False,
                network_mode='none',  # Isolate from network for security
                mem_limit='8g',
                cpu_count=4,
                runtime=runtime_config.get('runtime')
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
                # Container will be removed in finally block
                return {
                    'success': False,
                    'error': f"Timeout after {timeout}s"
                }
                
            finally:
                # Cleanup container - handle cases where container may already be removed
                try:
                    container.remove()
                except Exception as cleanup_error:
                    # Container may have already been removed or doesn't exist
                    # Only log if it's an unexpected error (not NotFound)
                    error_str = str(cleanup_error).lower()
                    if 'not found' not in error_str and 'no such container' not in error_str:
                        logger.debug(f"Container cleanup note: {cleanup_error}")
                    
        except Exception as e:
            logger.error(f"Error running container: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def pull_image(self, image: str):
        """Pull Docker image if not exists"""
        if not self.client:
            raise RuntimeError("Container runtime not available")
        
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
        if not self.client:
            return []
        
        try:
            images = self.client.images.list()
            return [img.tags[0] if img.tags else img.id for img in images]
        except Exception as e:
            logger.error(f"Failed to list images: {e}")
            return []
            
    def cleanup_old_containers(self):
        """Remove old stopped containers"""
        if not self.client:
            return
        
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
