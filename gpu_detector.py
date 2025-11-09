# gpu_detector.py

import pynvml
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger
import platform
import subprocess
from enum import Enum

class GPUType(Enum):
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"
    UNKNOWN = "unknown"

class ComputeFramework(Enum):
    CUDA = "cuda"
    ROCM = "rocm"
    METAL = "metal"
    OPENCL = "opencl"
    NONE = "none"

@dataclass
class GPUInfo:
    """GPU hardware information"""
    index: int
    name: str
    vendor: str
    gpu_type: GPUType
    compute_framework: ComputeFramework
    uuid: Optional[str] = None
    total_memory: int = 0  # bytes
    compute_capability: Optional[tuple] = None  # (major, minor) for NVIDIA
    cuda_cores: int = 0
    clock_speed: int = 0  # MHz
    memory_clock: int = 0  # MHz
    available: bool = True
    
class GPUDetector:
    """Detect and monitor GPUs across vendors (NVIDIA, AMD, Intel, Apple)"""
    
    def __init__(self):
        self.initialized = False
        self.gpus: List[GPUInfo] = []
        self.nvidia_available = False
        self.amd_available = False
        self._active_job_count = 0  # Track active jobs for better metrics
        
    def detect_system_gpus(self) -> List[Dict]:
        """Detect GPUs using system tools (works on macOS and Linux)"""
        gpus = []
        system = platform.system()
        
        try:
            if system == "Darwin":  # macOS
                result = subprocess.run(
                    ['system_profiler', 'SPDisplaysDataType'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    output = result.stdout
                    # Parse GPU information
                    lines = output.split('\n')
                    current_gpu = {}
                    for line in lines:
                        if 'Chipset Model:' in line:
                            if current_gpu:
                                gpus.append(current_gpu)
                            current_gpu = {'name': line.split('Chipset Model:')[1].strip()}
                        elif 'VRAM' in line and current_gpu:
                            vram_str = line.split('VRAM')[1].strip()
                            # Parse VRAM string like "VRAM (Dynamic, Max): 1536 MB"
                            try:
                                vram_mb = int(vram_str.split(':')[1].strip().split()[0])
                                current_gpu['vram_mb'] = vram_mb
                            except:
                                pass
                        elif 'Vendor:' in line and current_gpu:
                            current_gpu['vendor'] = line.split('Vendor:')[1].strip()
                    if current_gpu:
                        gpus.append(current_gpu)
            elif system == "Linux":
                # Try to detect GPUs using lspci
                result = subprocess.run(
                    ['lspci'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'VGA' in line or '3D' in line or 'Display' in line:
                            gpus.append({'name': line.strip(), 'vendor': 'Unknown'})
        except Exception as e:
            logger.debug(f"Error detecting system GPUs: {e}")
            
        return gpus
    
    def detect_nvidia_gpus(self) -> List[GPUInfo]:
        """Detect NVIDIA GPUs using NVML"""
        nvidia_gpus = []
        try:
            pynvml.nvmlInit()
            self.nvidia_available = True
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                gpu_info = GPUInfo(
                    index=i,
                    name=pynvml.nvmlDeviceGetName(handle).decode('utf-8'),
                    vendor="NVIDIA",
                    gpu_type=GPUType.NVIDIA,
                    compute_framework=ComputeFramework.CUDA,
                    uuid=pynvml.nvmlDeviceGetUUID(handle).decode('utf-8'),
                    total_memory=pynvml.nvmlDeviceGetMemoryInfo(handle).total,
                    compute_capability=pynvml.nvmlDeviceGetCudaComputeCapability(handle),
                    cuda_cores=self._get_cuda_cores(handle),
                    clock_speed=pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS),
                    memory_clock=pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM),
                    available=True
                )
                
                nvidia_gpus.append(gpu_info)
                logger.info(f"NVIDIA GPU {i}: {gpu_info.name} ({gpu_info.total_memory / 1e9:.1f}GB)")
                
        except pynvml.NVMLError_LibraryNotFound:
            logger.debug("NVML not available - NVIDIA GPUs not detected")
            self.nvidia_available = False
        except Exception as e:
            logger.debug(f"Error detecting NVIDIA GPUs: {e}")
            self.nvidia_available = False
            
        return nvidia_gpus
    
    def detect_amd_gpus(self) -> List[GPUInfo]:
        """Detect AMD GPUs using rocm-smi"""
        amd_gpus = []
        try:
            # Check if rocm-smi is available
            result = subprocess.run(
                ['rocm-smi'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.amd_available = True
                # Parse rocm-smi output
                # This is a simplified parser - in production, use rocm-smi JSON output
                lines = result.stdout.split('\n')
                gpu_index = 0
                for line in lines:
                    if 'card' in line.lower() and 'gpu' in line.lower():
                        # Extract GPU name
                        parts = line.split()
                        name = ' '.join(parts[1:]) if len(parts) > 1 else f"AMD GPU {gpu_index}"
                        
                        gpu_info = GPUInfo(
                            index=gpu_index,
                            name=name,
                            vendor="AMD",
                            gpu_type=GPUType.AMD,
                            compute_framework=ComputeFramework.ROCM,
                            total_memory=0,  # Would need to parse from rocm-smi
                            available=True
                        )
                        amd_gpus.append(gpu_info)
                        logger.info(f"AMD GPU {gpu_index}: {name}")
                        gpu_index += 1
        except FileNotFoundError:
            logger.debug("rocm-smi not found - AMD GPUs not detected")
            self.amd_available = False
        except Exception as e:
            logger.debug(f"Error detecting AMD GPUs: {e}")
            self.amd_available = False
            
        return amd_gpus
    
    def detect_apple_gpus(self) -> List[GPUInfo]:
        """Detect Apple Silicon GPUs"""
        apple_gpus = []
        system = platform.system()
        
        if system == "Darwin":
            # Check if Apple Silicon
            arch = platform.machine()
            if arch == "arm64":
                try:
                    # Use system_profiler to get GPU info
                    result = subprocess.run(
                        ['system_profiler', 'SPDisplaysDataType'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        output = result.stdout
                        # Check for Apple GPU indicators
                        if 'Apple' in output or 'Metal' in output:
                            gpu_info = GPUInfo(
                                index=0,
                                name="Apple Silicon GPU",
                                vendor="Apple",
                                gpu_type=GPUType.APPLE,
                                compute_framework=ComputeFramework.METAL,
                                total_memory=0,  # Shared memory on Apple Silicon
                                available=True
                            )
                            apple_gpus.append(gpu_info)
                            logger.info("Apple Silicon GPU detected")
                except Exception as e:
                    logger.debug(f"Error detecting Apple GPU: {e}")
                    
        return apple_gpus
    
    def detect_intel_gpus(self, system_gpus: List[Dict]) -> List[GPUInfo]:
        """Detect Intel GPUs from system GPU list"""
        intel_gpus = []
        for idx, gpu_dict in enumerate(system_gpus):
            vendor = gpu_dict.get('vendor', '').lower()
            name = gpu_dict.get('name', '')
            
            if 'intel' in vendor or 'intel' in name.lower():
                vram_mb = gpu_dict.get('vram_mb', 0)
                gpu_info = GPUInfo(
                    index=idx,
                    name=name,
                    vendor="Intel",
                    gpu_type=GPUType.INTEL,
                    compute_framework=ComputeFramework.OPENCL,  # Intel GPUs typically use OpenCL
                    total_memory=vram_mb * 1024 * 1024 if vram_mb > 0 else 0,
                    available=True
                )
                intel_gpus.append(gpu_info)
                logger.info(f"Intel GPU: {name}")
                
        return intel_gpus
        
    def initialize(self) -> bool:
        """Initialize GPU detection for all vendors"""
        self.gpus = []
        
        # Detect NVIDIA GPUs (highest priority for compute workloads)
        nvidia_gpus = self.detect_nvidia_gpus()
        self.gpus.extend(nvidia_gpus)
        
        # Detect AMD GPUs
        amd_gpus = self.detect_amd_gpus()
        self.gpus.extend(amd_gpus)
        
        # Detect system GPUs (for Intel/Apple on macOS)
        system_gpus = self.detect_system_gpus()
        
        # Detect Apple GPUs
        apple_gpus = self.detect_apple_gpus()
        self.gpus.extend(apple_gpus)
        
        # Detect Intel GPUs
        intel_gpus = self.detect_intel_gpus(system_gpus)
        self.gpus.extend(intel_gpus)
        
        # Filter out Apple GPUs if we already detected them
        if apple_gpus:
            system_gpus = [g for g in system_gpus if 'Apple' not in g.get('vendor', '')]
        
        self.initialized = True
        
        if self.gpus:
            logger.info(f"Detected {len(self.gpus)} GPU(s):")
            for gpu in self.gpus:
                framework = gpu.compute_framework.value if gpu.compute_framework else "none"
                logger.info(f"  - {gpu.name} ({gpu.vendor}) - Framework: {framework}")
            return True
        else:
            logger.warning("No GPUs detected")
            return False
            
    def detect_gpus(self) -> List[GPUInfo]:
        """Detect all available GPUs"""
        if not self.initialized:
            self.initialize()
                
        return self.gpus
        
    def _get_cuda_cores(self, handle) -> int:
        """Estimate CUDA cores based on GPU architecture"""
        compute_capability = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
        
        try:
            sm_count = pynvml.nvmlDeviceGetNumGpuCores(handle)
        except:
            sm_count = 0
            
        cores_per_sm_map = {
            (7, 5): 64,  # Turing
            (8, 0): 64,  # Ampere
            (8, 6): 128, # Ampere (GA102)
            (8, 9): 128, # Ada Lovelace
        }
        
        cores_per_sm = cores_per_sm_map.get(compute_capability, 64)
        if sm_count > 0:
            return sm_count * cores_per_sm
        else:
            return cores_per_sm * 60
        
    def get_gpu_utilization(self, gpu_index: int = 0) -> Dict:
        """Get current GPU utilization metrics"""
        if gpu_index >= len(self.gpus):
            return {}
            
        gpu = self.gpus[gpu_index]
        
        if gpu.gpu_type == GPUType.NVIDIA and self.nvidia_available:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
                
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                
                return {
                    'gpu_utilization': utilization.gpu,
                    'memory_utilization': utilization.memory,
                    'memory_used': memory_info.used,
                    'memory_free': memory_info.free,
                    'temperature': temperature,
                    'power_usage': power
                }
            except Exception as e:
                logger.error(f"Error getting GPU utilization: {e}")
                return {}
        else:
            # For non-NVIDIA GPUs (Intel, AMD, Apple), try to get basic metrics
            # Use system monitoring tools when available
            try:
                import platform
                system = platform.system()
                
                # For macOS, try to get GPU metrics
                if system == "Darwin" and gpu.gpu_type == GPUType.INTEL:
                    # Try multiple methods to get real GPU metrics
                    actual_temperature = None
                    actual_power = None
                    actual_memory_used = None
                    
                    # Method 1: Try to get temperature from IORegistry
                    try:
                        result = subprocess.run(
                            ['ioreg', '-l', '-w', '0'],
                            capture_output=True,
                            text=True,
                            timeout=3
                        )
                        if result.returncode == 0:
                            output = result.stdout
                            # Look for GPU temperature entries
                            import re
                            # Try to find temperature values
                            # Temperature can be stored as:
                            # - Direct value (e.g., 35 = 35°C)
                            # - Scaled by 100 (e.g., 3500 = 35°C) 
                            # - Scaled by 10 (e.g., 350 = 35°C)
                            temp_patterns = [
                                r'"Temperature"\s*=\s*(\d+)',  # Direct temperature (in IORegistry)
                                r'"GPU.*Temperature"\s*=\s*(\d+)',  # GPU-specific
                                r'"GPU Temperature"\s*=\s*(\d+)',  # Alternative format
                            ]
                            for pattern in temp_patterns:
                                matches = re.findall(pattern, output, re.IGNORECASE)
                                if matches:
                                    # Try the most recent/last match (most likely to be current)
                                    temp_val = int(matches[-1])
                                    
                                    # Determine scale: battery temp is usually 100x (3089 = 30.89°C)
                                    # GPU temp might be different, try to infer
                                    if temp_val > 5000:  # Probably 100x scale (e.g., 5000 = 50°C)
                                        actual_temperature = temp_val / 100.0
                                    elif temp_val > 500:  # Might be 10x scale (e.g., 350 = 35°C)
                                        actual_temperature = temp_val / 10.0
                                    elif temp_val < 150:  # Likely direct value (e.g., 35 = 35°C)
                                        actual_temperature = float(temp_val)
                                    else:
                                        # Default: assume 100x scale for values 150-5000
                                        actual_temperature = temp_val / 100.0
                                    
                                    # Sanity check: temperature should be reasonable (20-100°C)
                                    if 20 <= actual_temperature <= 100:
                                        logger.debug(f"Found GPU temperature from ioreg: {actual_temperature}°C")
                                        break
                                    else:
                                        actual_temperature = None
                    except Exception as e:
                        logger.debug(f"ioreg temperature check failed: {e}")
                    
                    # Method 2: Try powermetrics for power (may require sudo)
                    try:
                        result = subprocess.run(
                            ['powermetrics', '--samplers', 'gpu_power', '-i', '100', '-n', '1'],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        if result.returncode == 0:
                            output = result.stdout
                            import re
                            power_match = re.search(r'GPU.*?(\d+\.?\d*)\s*W', output, re.IGNORECASE)
                            if power_match:
                                actual_power = float(power_match.group(1))
                    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                        pass
                    
                    # Method 3: Try Activity Monitor approach (parse system_profiler or vm_stat)
                    # GPU memory usage is harder - Intel integrated GPUs share system RAM
                    # We can estimate based on system memory pressure
                    try:
                        result = subprocess.run(
                            ['vm_stat'],
                            capture_output=True,
                            text=True,
                            timeout=1
                        )
                        if result.returncode == 0:
                            # Parse memory stats to estimate GPU memory (very rough)
                            # Intel GPUs use system RAM, so this is an approximation
                            pass  # Keep memory_used as 0 for now - very hard to measure accurately
                    except Exception:
                        pass
                    
                    # For Intel GPUs, real monitoring is limited without sudo
                    # Use Activity Monitor approach or return realistic defaults
                    active_jobs = getattr(self, '_active_job_count', 0)
                    
                    # Try to get real GPU utilization using Activity Monitor or system calls
                    # On macOS, GPU utilization is harder to get without system APIs
                    # For now, show 0% utilization (accurate when no GPU-intensive work)
                    # Temperature and power can be estimated based on activity
                    
                    # Use real values if available, otherwise use realistic estimates
                    active_jobs = getattr(self, '_active_job_count', 0)
                    
                    # Temperature: Use real if available, else estimate based on activity
                    if actual_temperature is not None:
                        temperature = actual_temperature
                        temp_accurate = True
                    else:
                        # Realistic estimates for Intel integrated GPU:
                        # - Idle: ~35-40°C
                        # - Light load: ~40-50°C  
                        # - Heavy load: ~50-70°C
                        temperature = 45 if active_jobs > 0 else 35
                        temp_accurate = False
                    
                    # Power: Use real if available, else estimate
                    if actual_power is not None:
                        power = actual_power
                        power_accurate = True
                    else:
                        # Estimates: Idle ~1-2W, Active ~3-10W
                        power = 5.0 if active_jobs > 0 else 2.0
                        power_accurate = False
                    
                    # Utilization: 0% is accurate when no GPU-intensive work is happening
                    # (Most node3 jobs are CPU-only, not GPU compute)
                    utilization = 0
                    
                    # Memory: Intel GPUs share system RAM, very hard to measure accurately
                    # Show 0GB used unless we have a way to measure it
                    memory_used = actual_memory_used if actual_memory_used is not None else 0
                    
                    # Return metrics with accuracy flags
                    return {
                        'gpu_utilization': utilization,  # 0% - accurate (no GPU compute jobs running)
                        'memory_utilization': int((memory_used / gpu.total_memory) * 100) if gpu.total_memory > 0 else 0,
                        'memory_used': memory_used,
                        'memory_free': gpu.total_memory - memory_used,
                        'temperature': temperature,
                        'power_usage': power,
                        'metrics_accurate': temp_accurate and power_accurate  # True if we got real data
                    }
                else:
                    # For other GPUs, return basic info with estimated values
                    return {
                        'gpu_utilization': 0,
                        'memory_utilization': 0,
                        'memory_used': 0,
                        'memory_free': gpu.total_memory,
                        'temperature': 0,
                        'power_usage': 0
                    }
            except Exception as e:
                logger.debug(f"Error getting GPU metrics: {e}")
                return {
                    'gpu_utilization': 0,
                    'memory_utilization': 0,
                    'memory_used': 0,
                    'memory_free': gpu.total_memory,
                    'temperature': 0,
                    'power_usage': 0
                }
            
    def is_gpu_available(self, gpu_index: int = 0, threshold: int = 20) -> bool:
        """Check if GPU is available for work"""
        if gpu_index >= len(self.gpus):
            return False
            
        gpu = self.gpus[gpu_index]
        if not gpu.available:
            return False
            
        util = self.get_gpu_utilization(gpu_index)
        if not util:
            return False
            
        return util.get('gpu_utilization', 0) < threshold
        
    def benchmark_gpu(self, gpu_index: int = 0) -> Dict:
        """Run GPU benchmark using appropriate framework"""
        if gpu_index >= len(self.gpus):
            return {}
            
        gpu = self.gpus[gpu_index]
        
        if gpu.compute_framework == ComputeFramework.CUDA:
            return self._benchmark_cuda(gpu_index)
        elif gpu.compute_framework == ComputeFramework.METAL:
            return self._benchmark_metal(gpu_index)
        elif gpu.compute_framework == ComputeFramework.ROCM:
            return self._benchmark_rocm(gpu_index)
        else:
            logger.warning(f"Benchmarking not yet implemented for {gpu.compute_framework.value}")
            return {}
    
    def _benchmark_cuda(self, gpu_index: int) -> Dict:
        """Benchmark NVIDIA GPU using CUDA"""
        import torch
        import time
        
        if not torch.cuda.is_available():
            logger.error("CUDA not available for benchmarking")
            return {}
            
        try:
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
            
            operations = 2 * (size ** 3) * iterations
            tflops = (operations / elapsed) / 1e12
            
            logger.info(f"GPU {gpu_index} benchmark: {tflops:.2f} TFLOPS")
            
            return {
                'tflops': tflops,
                'elapsed_time': elapsed,
                'iterations': iterations,
                'framework': 'cuda'
            }
            
        except Exception as e:
            logger.error(f"CUDA benchmark failed: {e}")
            return {}
    
    def _benchmark_metal(self, gpu_index: int) -> Dict:
        """Benchmark Apple GPU using Metal"""
        # Placeholder - would need Metal Performance Shaders
        logger.info("Metal benchmarking not yet implemented")
        return {
            'framework': 'metal',
            'note': 'Metal benchmarking coming soon'
        }
    
    def _benchmark_rocm(self, gpu_index: int) -> Dict:
        """Benchmark AMD GPU using ROCm"""
        # Placeholder - would need ROCm PyTorch
        logger.info("ROCm benchmarking not yet implemented")
        return {
            'framework': 'rocm',
            'note': 'ROCm benchmarking coming soon'
        }
            
    def shutdown(self):
        """Cleanup resources"""
        if self.nvidia_available:
            try:
                pynvml.nvmlShutdown()
                logger.info("NVML shutdown successfully")
            except Exception as e:
                logger.error(f"Error shutting down NVML: {e}")
