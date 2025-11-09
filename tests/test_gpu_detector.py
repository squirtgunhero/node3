# tests/test_gpu_detector.py

import pytest
from gpu_detector import GPUDetector

def test_gpu_detection():
    """Test GPU detection"""
    detector = GPUDetector()
    gpus = detector.detect_gpus()
    # Note: This test will fail if no GPUs are available
    # In CI/CD, this should be skipped or mocked
    if len(gpus) == 0:
        pytest.skip("No GPUs available for testing")
    
    assert len(gpus) > 0
    assert gpus[0].name is not None
    assert gpus[0].total_memory > 0
    
def test_gpu_utilization():
    """Test GPU utilization monitoring"""
    detector = GPUDetector()
    detector.detect_gpus()
    
    if len(detector.gpus) == 0:
        pytest.skip("No GPUs available for testing")
    
    util = detector.get_gpu_utilization(0)
    assert 'gpu_utilization' in util
    assert 0 <= util['gpu_utilization'] <= 100
    assert 'memory_used' in util
    assert 'temperature' in util

