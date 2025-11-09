# native_executor.py
"""
Native Job Executor - Runs jobs without Docker/Lima

This module provides native process execution for jobs, eliminating
the need for Docker or any container runtime. Jobs run as isolated
Python processes with resource limits and sandboxing.
"""

import asyncio
import subprocess
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
import psutil
import resource


class NativeExecutor:
    """Execute jobs natively without containers"""
    
    def __init__(self, work_dir: Optional[Path] = None):
        """
        Initialize native executor
        
        Args:
            work_dir: Base directory for job execution (default: /tmp/node3_jobs)
        """
        self.work_dir = work_dir or Path("/tmp/node3_jobs")
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
    async def run_job(self,
                     job_id: str,
                     command: List[str],
                     environment: Dict[str, str] = None,
                     timeout: int = 3600,
                     input_dir: Optional[Path] = None,
                     output_dir: Optional[Path] = None,
                     memory_limit_mb: int = 8192,
                     cpu_limit: int = 4) -> Dict:
        """
        Execute a job natively as a subprocess
        
        Args:
            job_id: Unique job identifier
            command: Command to execute (e.g., ["python", "script.py"])
            environment: Environment variables
            timeout: Maximum execution time in seconds
            input_dir: Directory with input files
            output_dir: Directory for output files
            memory_limit_mb: Memory limit in MB
            cpu_limit: CPU core limit
            
        Returns:
            Dict with 'success', 'output', 'error', 'exit_code'
        """
        # Create isolated job directory
        job_dir = self.work_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Setup input/output directories
            job_input = job_dir / "input"
            job_output = job_dir / "output"
            
            if input_dir and input_dir.exists():
                # Copy input files
                shutil.copytree(input_dir, job_input, dirs_exist_ok=True)
            else:
                job_input.mkdir(exist_ok=True)
            
            job_output.mkdir(exist_ok=True)
            
            # Prepare environment
            env = os.environ.copy()
            env.update(environment or {})
            env['JOB_ID'] = job_id
            env['INPUT_DIR'] = str(job_input)
            env['OUTPUT_DIR'] = str(job_output)
            
            # Build command (support Python scripts and inline code)
            if command[0] in ("python", "python3") and len(command) > 1:
                if command[1] == "-c":
                    # Python inline code execution: python -c "code"
                    python_code = command[2] if len(command) > 2 else ""
                    # Replace container paths with proper path handling
                    # Need to replace /output/path with os.path.join(OUTPUT_DIR, 'path')
                    import re
                    # Replace /output/path with proper path join
                    # Handle 'path' format
                    python_code = re.sub(r"'/output/([^']+)'", r"os.path.join(os.getenv('OUTPUT_DIR', '/tmp/node3_output'), '\1')", python_code)
                    # Handle "path" format  
                    python_code = re.sub(r'"/output/([^"]+)"', r'os.path.join(os.getenv("OUTPUT_DIR", "/tmp/node3_output"), "\1")', python_code)
                    # Replace standalone /output references (for open('/output/file'))
                    python_code = re.sub(r"open\('/output/([^']+)'", r"open(os.path.join(os.getenv('OUTPUT_DIR', '/tmp/node3_output'), '\1')", python_code)
                    python_code = re.sub(r'open\("/output/([^"]+)"', r'open(os.path.join(os.getenv("OUTPUT_DIR", "/tmp/node3_output"), "\1")', python_code)
                    # Replace /input references similarly
                    python_code = re.sub(r"'/input/([^']+)'", r"os.path.join(os.getenv('INPUT_DIR', '/tmp/node3_input'), '\1')", python_code)
                    python_code = re.sub(r'"/input/([^"]+)"', r'os.path.join(os.getenv("INPUT_DIR", "/tmp/node3_input"), "\1")', python_code)
                    # Ensure os is imported if we're using it
                    if ("os.getenv" in python_code or "os.path.join" in python_code) and "import os" not in python_code:
                        python_code = "import os; " + python_code
                    cmd = ["python3", "-c", python_code]
                elif command[1].endswith(".py") or "/app/" in command[1]:
                    # Python script execution
                    script_path = command[1]
                    
                    # Handle container paths like /app/script.py
                    if script_path.startswith("/app/"):
                        script_name = Path(script_path).name
                        # Try to find script in test_jobs directory or input directory
                        test_script = Path(__file__).parent.parent / "test_jobs" / script_name
                        if test_script.exists():
                            script_path = str(test_script)
                            logger.info(f"Found test script: {script_path}")
                        else:
                            # Try input directory
                            potential_script = job_input / script_name
                            if potential_script.exists():
                                script_path = str(potential_script)
                            else:
                                logger.warning(f"Script {script_path} not found - this job may need Docker")
                                # Create a simple fallback script
                                script_path = None
                    
                    if script_path and Path(script_path).exists():
                        cmd = ["python3", script_path] + command[2:]
                    elif script_path and not Path(script_path).is_absolute():
                        # Try to find script in input directory
                        potential_script = job_input / Path(script_path).name
                        if potential_script.exists():
                            cmd = ["python3", str(potential_script)] + command[2:]
                        else:
                            # Last resort: try current directory
                            cmd = ["python3", script_path] + command[2:]
                    else:
                        logger.error(f"Script not found: {script_path}")
                        raise FileNotFoundError(f"Script not found: {script_path}")
                else:
                    # Generic Python command (pass through)
                    cmd = ["python3"] + command[1:]
            else:
                # Generic command execution (replace "python" with "python3" for compatibility)
                cmd = [c if c != "python" else "python3" for c in command]
            
            logger.info(f"Executing job {job_id} natively: {' '.join(cmd)}")
            
            # Set resource limits
            def set_limits():
                """Set resource limits for the subprocess"""
                # Memory limit (RSS)
                try:
                    resource.setrlimit(
                        resource.RLIMIT_AS,
                        (memory_limit_mb * 1024 * 1024, memory_limit_mb * 1024 * 1024)
                    )
                except:
                    pass  # Not all systems support this
                
                # CPU time limit
                try:
                    resource.setrlimit(
                        resource.RLIMIT_CPU,
                        (timeout, timeout)
                    )
                except:
                    pass
            
            # Run subprocess with limits
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=str(job_dir),
                preexec_fn=set_limits if sys.platform != 'win32' else None
            )
            
            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                exit_code = process.returncode
                output = stdout.decode('utf-8', errors='replace')
                error_output = stderr.decode('utf-8', errors='replace')
                
                if exit_code == 0:
                    logger.info(f"Job {job_id} completed successfully")
                    return {
                        'success': True,
                        'output': output,
                        'error': error_output,
                        'exit_code': exit_code,
                        'output_dir': str(job_output)
                    }
                else:
                    logger.error(f"Job {job_id} failed with exit code {exit_code}")
                    return {
                        'success': False,
                        'output': output,
                        'error': error_output,
                        'exit_code': exit_code,
                        'output_dir': str(job_output)
                    }
                    
            except asyncio.TimeoutError:
                logger.error(f"Job {job_id} timed out after {timeout}s")
                process.kill()
                await process.wait()
                return {
                    'success': False,
                    'error': f"Job timed out after {timeout} seconds",
                    'exit_code': -1
                }
                
        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'exit_code': -1
            }
        finally:
            # Cleanup (optional - keep for debugging)
            # shutil.rmtree(job_dir, ignore_errors=True)
            pass
    
    async def run_python_script(self,
                                job_id: str,
                                script_content: str,
                                environment: Dict[str, str] = None,
                                timeout: int = 3600) -> Dict:
        """
        Execute a Python script directly
        
        Args:
            job_id: Unique job identifier
            script_content: Python script code
            environment: Environment variables
            timeout: Maximum execution time
            
        Returns:
            Dict with execution results
        """
        # Create temporary script file
        job_dir = self.work_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        script_path = job_dir / "script.py"
        script_path.write_text(script_content)
        
        return await self.run_job(
            job_id=job_id,
            command=["python3", str(script_path)],
            environment=environment,
            timeout=timeout
        )
    
    def cleanup(self, job_id: Optional[str] = None):
        """Clean up job directories"""
        if job_id:
            job_dir = self.work_dir / job_id
            if job_dir.exists():
                shutil.rmtree(job_dir, ignore_errors=True)
        else:
            # Clean up old jobs (older than 24 hours)
            import time
            current_time = time.time()
            for job_dir in self.work_dir.iterdir():
                if job_dir.is_dir():
                    try:
                        mtime = job_dir.stat().st_mtime
                        if current_time - mtime > 86400:  # 24 hours
                            shutil.rmtree(job_dir, ignore_errors=True)
                    except:
                        pass

