#!/usr/bin/env python3
"""
Test agent job manager connection to mock marketplace
"""
import asyncio
import sys
from loguru import logger
from job_manager import JobManager

async def test_job_manager():
    """Test job manager connection"""
    
    logger.info("=" * 60)
    logger.info("Testing Agent Job Manager Connection")
    logger.info("=" * 60)
    
    marketplace_url = "http://127.0.0.1:8000"
    
    # Create job manager (without Docker for testing)
    job_manager = JobManager(
        marketplace_url=marketplace_url,
        api_key="test-key",
        gpu_info={
            'name': 'Test GPU',
            'vendor': 'Test',
            'gpu_type': 'test',
            'compute_framework': 'test',
            'total_memory': 4294967296,  # 4GB
            'compute_capability': None
        },
        docker_manager=None  # No Docker for this test
    )
    
    logger.info(f"\nMarketplace URL: {marketplace_url}")
    logger.info("Polling marketplace for jobs...\n")
    
    try:
        jobs = await job_manager.poll_marketplace()
        
        if jobs:
            logger.success(f"✅ Successfully retrieved {len(jobs)} job(s)!")
            
            for i, job in enumerate(jobs, 1):
                logger.info(f"\nJob {i}:")
                logger.info(f"  - Job ID: {job.job_id}")
                logger.info(f"  - Type: {job.job_type}")
                logger.info(f"  - Docker Image: {job.docker_image}")
                logger.info(f"  - Reward: {job.reward} SOL")
                logger.info(f"  - Status: {job.status}")
                
                # Verify unique IDs
                if i > 1:
                    prev_job = jobs[i-2]
                    if job.job_id == prev_job.job_id:
                        logger.warning(f"  ⚠️  WARNING: Duplicate job ID detected!")
                    else:
                        logger.success(f"  ✅ Unique job ID verified")
        else:
            logger.warning("⚠️  No jobs returned")
            logger.info("  This might be normal if GPU memory requirement not met")
        
        logger.info("\n" + "=" * 60)
        logger.success("✅ Agent job manager test passed!")
        logger.info("\nNext: Start full agent with:")
        logger.info("  MARKETPLACE_URL=http://127.0.0.1:8000 python main.py")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to poll marketplace: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO")
    
    success = asyncio.run(test_job_manager())
    sys.exit(0 if success else 1)

