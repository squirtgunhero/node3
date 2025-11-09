#!/usr/bin/env python3
"""
Test script to verify agent connection to mock marketplace
"""
import asyncio
import httpx
import json
from loguru import logger

MARKETPLACE_URL = "http://127.0.0.1:8000"

async def test_marketplace_connection():
    """Test connecting to mock marketplace"""
    
    logger.info("=" * 60)
    logger.info("Testing Mock Marketplace Connection")
    logger.info("=" * 60)
    
    # Test 1: Check marketplace is running
    logger.info("\n1. Checking marketplace status...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MARKETPLACE_URL}/")
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✅ Marketplace is running!")
                logger.info(f"   Status: {data.get('status')}")
                logger.info(f"   Message: {data.get('message')}")
            else:
                logger.error(f"❌ Marketplace returned status {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ Failed to connect to marketplace: {e}")
        logger.error("   Make sure mock_marketplace.py is running!")
        return False
    
    # Test 2: Request available jobs
    logger.info("\n2. Requesting available jobs...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MARKETPLACE_URL}/api/jobs/available",
                json={
                    'gpu_model': 'Test GPU',
                    'gpu_vendor': 'Test',
                    'gpu_type': 'test',
                    'compute_framework': 'test',
                    'gpu_memory': 4294967296,  # 4GB
                    'max_concurrent_jobs': 1
                },
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('jobs', [])
                logger.success(f"✅ Successfully requested jobs!")
                logger.info(f"   Jobs returned: {len(jobs)}")
                
                if jobs:
                    job = jobs[0]
                    logger.info(f"\n   Job Details:")
                    logger.info(f"   - Job ID: {job.get('job_id')}")
                    logger.info(f"   - Type: {job.get('job_type')}")
                    logger.info(f"   - Docker Image: {job.get('docker_image')}")
                    logger.info(f"   - Reward: {job.get('reward')} SOL")
                    logger.info(f"   - GPU Memory Required: {job.get('gpu_memory_required')} bytes")
                else:
                    logger.warning("   No jobs available (GPU memory requirement not met)")
                
                return True
            else:
                logger.error(f"❌ Failed to get jobs: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
    except Exception as e:
        logger.error(f"❌ Failed to request jobs: {e}")
        return False
    
    # Test 3: Check marketplace status endpoint
    logger.info("\n3. Checking marketplace status...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MARKETPLACE_URL}/api/status")
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✅ Marketplace status retrieved!")
                logger.info(f"   Available jobs: {data.get('available_jobs')}")
                logger.info(f"   Accepted jobs: {data.get('accepted_jobs')}")
                logger.info(f"   Registered agents: {data.get('registered_agents')}")
                if data.get('agents'):
                    logger.info(f"   Agents: {', '.join(data.get('agents', []))}")
                return True
            else:
                logger.error(f"❌ Failed to get status: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ Failed to get status: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting marketplace connection test...")
    logger.info(f"Marketplace URL: {MARKETPLACE_URL}")
    logger.info("")
    
    success = asyncio.run(test_marketplace_connection())
    
    logger.info("")
    logger.info("=" * 60)
    if success:
        logger.success("✅ All tests passed!")
        logger.info("\nNext steps:")
        logger.info("1. Start the agent with: MARKETPLACE_URL=http://127.0.0.1:8000 python main.py")
        logger.info("2. Or set MARKETPLACE_URL in your .env file")
    else:
        logger.error("❌ Some tests failed!")
        logger.info("\nMake sure:")
        logger.info("1. Mock marketplace is running: python mock_marketplace.py")
        logger.info("2. Marketplace is accessible at http://127.0.0.1:8000")
    logger.info("=" * 60)

