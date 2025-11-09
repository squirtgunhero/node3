#!/usr/bin/env python3
"""
Test script to verify job execution works
Tests the complete flow: marketplace -> job acceptance -> execution -> completion
"""

import asyncio
import httpx
import json
import time
import sys
from pathlib import Path
from loguru import logger

MARKETPLACE_URL = "http://127.0.0.1:8000"
TEST_OUTPUT_DIR = Path("/tmp/node3_test_output")

async def test_marketplace_connection():
    """Test if marketplace is accessible"""
    logger.info("Testing marketplace connection...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MARKETPLACE_URL}/")
            if response.status_code == 200:
                logger.info("✓ Marketplace is accessible")
                return True
            else:
                logger.error(f"✗ Marketplace returned status {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"✗ Failed to connect to marketplace: {e}")
        logger.error("Make sure mock_marketplace.py is running: python mock_marketplace.py")
        return False

async def test_get_jobs():
    """Test getting available jobs"""
    logger.info("Testing job retrieval...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MARKETPLACE_URL}/api/jobs/available",
                json={
                    "gpu_model": "Test GPU",
                    "gpu_vendor": "Test",
                    "gpu_type": "test",
                    "compute_framework": "none",
                    "gpu_memory": 0,  # CPU-only jobs
                    "max_concurrent_jobs": 1
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", [])
                logger.info(f"✓ Retrieved {len(jobs)} job(s)")
                
                for job in jobs:
                    logger.info(f"  - Job {job['job_id'][:8]}... ({job['job_type']}) - {job['reward']} SOL")
                
                return jobs
            else:
                logger.error(f"✗ Failed to get jobs: {response.status_code}")
                logger.error(response.text)
                return []
    except Exception as e:
        logger.error(f"✗ Error getting jobs: {e}")
        return []

async def test_accept_job(job_id: str):
    """Test accepting a job"""
    logger.info(f"Testing job acceptance: {job_id[:8]}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MARKETPLACE_URL}/api/jobs/{job_id}/accept",
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.info(f"✓ Job accepted successfully")
                return True
            else:
                logger.error(f"✗ Failed to accept job: {response.status_code}")
                logger.error(response.text)
                return False
    except Exception as e:
        logger.error(f"✗ Error accepting job: {e}")
        return False

async def test_complete_job(job_id: str):
    """Test reporting job completion"""
    logger.info(f"Testing job completion: {job_id[:8]}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MARKETPLACE_URL}/api/jobs/{job_id}/complete",
                json={
                    "status": "completed",
                    "started_at": time.time() - 10,
                    "completed_at": time.time(),
                    "duration": 10.0
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.info(f"✓ Job completion reported successfully")
                return True
            else:
                logger.error(f"✗ Failed to report completion: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"✗ Error reporting completion: {e}")
        return False

async def test_docker_execution():
    """Test if Docker can execute a simple container"""
    logger.info("Testing Docker execution...")
    try:
        import docker
        client = docker.from_env()
        client.ping()
        
        # Try running a simple test container
        logger.info("Running test container...")
        result = client.containers.run(
            "python:3.11-slim",
            command=["python", "-c", "print('Docker test successful!')"],
            remove=True,
            timeout=30
        )
        
        output = result.decode('utf-8').strip()
        logger.info(f"✓ Docker execution successful: {output}")
        return True
    except ImportError:
        logger.warning("✗ Docker Python library not available")
        return False
    except Exception as e:
        logger.warning(f"✗ Docker execution failed: {e}")
        logger.warning("  This is OK if Docker is not installed/running")
        return False

async def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("node3 Job Execution Test Suite")
    logger.info("=" * 60)
    logger.info("")
    
    results = {
        "marketplace_connection": False,
        "job_retrieval": False,
        "job_acceptance": False,
        "job_completion": False,
        "docker_execution": False
    }
    
    # Test 1: Marketplace connection
    results["marketplace_connection"] = await test_marketplace_connection()
    if not results["marketplace_connection"]:
        logger.error("\n✗ Cannot proceed without marketplace connection")
        logger.error("Start marketplace: python mock_marketplace.py")
        return 1
    
    logger.info("")
    
    # Test 2: Get jobs
    jobs = await test_get_jobs()
    results["job_retrieval"] = len(jobs) > 0
    
    if not results["job_retrieval"]:
        logger.error("\n✗ No jobs available")
        return 1
    
    logger.info("")
    
    # Test 3: Accept job
    test_job = jobs[0]
    results["job_acceptance"] = await test_accept_job(test_job["job_id"])
    
    logger.info("")
    
    # Test 4: Complete job
    if results["job_acceptance"]:
        results["job_completion"] = await test_complete_job(test_job["job_id"])
    
    logger.info("")
    
    # Test 5: Docker execution (optional)
    results["docker_execution"] = await test_docker_execution()
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status} - {test_name.replace('_', ' ').title()}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("")
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.info("")
        logger.warning("⚠ Some tests failed (see above for details)")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))


