#!/usr/bin/env python3
"""
End-to-End Integration Test
============================
Tests the complete flow: marketplace -> agent -> job execution -> payment

This test validates:
1. Marketplace is running and healthy
2. Agent can register with marketplace
3. Jobs can be posted to marketplace
4. Agent accepts and executes jobs
5. Payment is processed

Usage:
    # Start the integrated system first:
    python start_integrated_system.py
    
    # Then run this test in another terminal:
    python test_end_to_end.py
"""

import asyncio
import httpx
import sys
import time
from colorama import init, Fore, Style
import os

init(autoreset=True)

MARKETPLACE_URL = "http://localhost:8000"
AGENT_URL = "http://localhost:8080"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")  # Will be set by marketplace on startup

test_results = []

def print_test(name, passed, details=""):
    """Print test result"""
    global test_results
    test_results.append(passed)
    
    if passed:
        print(f"{Fore.GREEN}✓{Style.RESET_ALL} {name}")
        if details:
            print(f"  {Fore.CYAN}{details}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗{Style.RESET_ALL} {name}")
        if details:
            print(f"  {Fore.RED}{details}{Style.RESET_ALL}")
    return passed


async def test_marketplace_health():
    """Test marketplace is running"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MARKETPLACE_URL}/health", timeout=5.0)
            data = response.json()
            
            passed = (response.status_code == 200 and 
                     data['status'] == 'healthy' and
                     data['database'] == 'connected')
            
            details = f"Status: {data['status']}, DB: {data['database']}, Payments: {data['payment_system']}"
            return print_test("Marketplace is healthy", passed, details)
            
    except Exception as e:
        return print_test("Marketplace is healthy", False, str(e))


async def test_agent_online():
    """Test agent is online and responding"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AGENT_URL}/api/status", timeout=5.0)
            data = response.json()
            
            passed = response.status_code == 200 and 'gpus' in data
            gpu_info = data['gpus'][0]['name'] if data.get('gpus') else 'No GPU'
            details = f"GPU: {gpu_info}, Wallet: {data.get('wallet_address', 'N/A')[:12]}..."
            
            return print_test("Agent is online", passed, details)
            
    except Exception as e:
        return print_test("Agent is online", False, str(e))


async def test_agent_registered():
    """Test agent is registered in marketplace"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MARKETPLACE_URL}/api/marketplace/agents", timeout=5.0)
            data = response.json()
            
            agents = data.get('agents', [])
            passed = len(agents) > 0
            
            details = f"Registered agents: {len(agents)}"
            if agents:
                details += f" - {agents[0]['gpu_model']}"
            
            return print_test("Agent registered in marketplace", passed, details)
            
    except Exception as e:
        return print_test("Agent registered in marketplace", False, str(e))


async def test_create_test_job():
    """Test creating a job in the marketplace"""
    try:
        # Get admin API key from marketplace startup
        admin_key = os.getenv("ADMIN_API_KEY")
        if not admin_key:
            # Try to read from marketplace logs or use a default
            admin_key = "test_admin_key_dev"
        
        async with httpx.AsyncClient() as client:
            job_data = {
                "job_type": "test",
                "docker_image": "python:3.11-slim",
                "command": ["python", "-c", "print('Hello from node3 GPU!'); import time; time.sleep(2); print('Job complete!')"],
                "environment": {},
                "gpu_memory_required": 1000000000,  # 1GB
                "requires_gpu": True,
                "estimated_duration": 30,
                "timeout": 60,
                "reward": 0.0001,
                "input_data_url": "",
                "output_upload_url": ""
            }
            
            response = await client.post(
                f"{MARKETPLACE_URL}/api/admin/jobs/create",
                json=job_data,
                headers={"X-API-Key": admin_key},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get('job_id', '')
                details = f"Job ID: {job_id[:12]}..., Reward: 0.0001 SOL"
                
                # Store job_id for later tests
                global created_job_id
                created_job_id = job_id
                
                return print_test("Created test job in marketplace", True, details)
            else:
                return print_test("Created test job in marketplace", False, 
                                f"Status: {response.status_code}, {response.text[:100]}")
                
    except Exception as e:
        return print_test("Created test job in marketplace", False, str(e))


async def test_agent_accepts_job():
    """Test that agent accepts the job"""
    print(f"\n{Fore.YELLOW}⏳ Waiting for agent to accept job (max 30s)...{Style.RESET_ALL}")
    
    try:
        # Wait up to 30 seconds for agent to pick up the job
        for i in range(30):
            await asyncio.sleep(1)
            
            # Check agent's active jobs
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{AGENT_URL}/api/status", timeout=5.0)
                data = response.json()
                
                active_jobs = data.get('active_jobs', 0)
                if active_jobs > 0:
                    details = f"Agent accepted job (after {i+1}s)"
                    return print_test("Agent accepts job", True, details)
        
        return print_test("Agent accepts job", False, "Timeout waiting for job acceptance")
        
    except Exception as e:
        return print_test("Agent accepts job", False, str(e))


async def test_job_execution():
    """Test that job executes successfully"""
    print(f"\n{Fore.YELLOW}⏳ Waiting for job execution (max 60s)...{Style.RESET_ALL}")
    
    try:
        start_time = time.time()
        
        # Wait up to 60 seconds for job to complete
        for i in range(60):
            await asyncio.sleep(1)
            
            # Check job history
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{AGENT_URL}/api/jobs", timeout=5.0)
                data = response.json()
                
                jobs = data.get('jobs', [])
                completed_jobs = [j for j in jobs if j['status'] == 'completed']
                
                if completed_jobs:
                    duration = time.time() - start_time
                    job = completed_jobs[0]
                    details = f"Job completed in {duration:.1f}s, Reward: {job['reward']} SOL"
                    return print_test("Job executes successfully", True, details)
        
        return print_test("Job executes successfully", False, "Timeout waiting for job completion")
        
    except Exception as e:
        return print_test("Job executes successfully", False, str(e))


async def test_payment_processed():
    """Test that payment was processed"""
    print(f"\n{Fore.YELLOW}⏳ Waiting for payment (max 10s)...{Style.RESET_ALL}")
    
    try:
        # Wait a bit for payment to process
        await asyncio.sleep(5)
        
        # Check agent balance increased
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AGENT_URL}/api/status", timeout=5.0)
            data = response.json()
            
            # Check earnings
            earnings_response = await client.get(f"{AGENT_URL}/api/earnings", timeout=5.0)
            earnings_data = earnings_response.json()
            
            total_earnings = earnings_data.get('total_earnings', 0)
            passed = total_earnings > 0
            
            details = f"Total earnings: {total_earnings} SOL"
            return print_test("Payment processed", passed, details)
            
    except Exception as e:
        return print_test("Payment processed", False, str(e))


async def test_marketplace_stats():
    """Test marketplace statistics are updated"""
    try:
        admin_key = os.getenv("ADMIN_API_KEY", "test_admin_key_dev")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MARKETPLACE_URL}/api/admin/stats",
                headers={"X-API-Key": admin_key},
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                total_agents = data['agents']['total']
                total_jobs = data['jobs']['total']
                completed_jobs = data['jobs']['by_status'].get('completed', 0)
                
                passed = total_agents > 0 and total_jobs > 0
                details = f"Agents: {total_agents}, Jobs: {total_jobs}, Completed: {completed_jobs}"
                
                return print_test("Marketplace stats updated", passed, details)
            else:
                return print_test("Marketplace stats updated", False, f"Status: {response.status_code}")
                
    except Exception as e:
        return print_test("Marketplace stats updated", False, str(e))


async def main():
    """Run all end-to-end tests"""
    print("\n" + "="*60)
    print("  node³ End-to-End Integration Test")
    print("="*60 + "\n")
    
    print(f"Testing system at:")
    print(f"  Marketplace: {MARKETPLACE_URL}")
    print(f"  Agent: {AGENT_URL}\n")
    
    # Phase 1: System Health
    print(f"{Fore.YELLOW}Phase 1: System Health{Style.RESET_ALL}")
    await test_marketplace_health()
    await test_agent_online()
    await test_agent_registered()
    print()
    
    # Phase 2: Job Creation
    print(f"{Fore.YELLOW}Phase 2: Job Creation{Style.RESET_ALL}")
    await test_create_test_job()
    print()
    
    # Phase 3: Job Execution
    print(f"{Fore.YELLOW}Phase 3: Job Execution{Style.RESET_ALL}")
    await test_agent_accepts_job()
    await test_job_execution()
    print()
    
    # Phase 4: Payment & Stats
    print(f"{Fore.YELLOW}Phase 4: Payment & Stats{Style.RESET_ALL}")
    await test_payment_processed()
    await test_marketplace_stats()
    print()
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed ({percentage:.1f}%)")
    
    if passed == total:
        print(f"{Fore.GREEN}✅ All end-to-end tests passed!{Style.RESET_ALL}")
        print("\n🎉 Your node³ system is fully operational!")
        print("\n📋 System is ready for:")
        print("  • Accepting real marketplace jobs")
        print("  • Executing GPU workloads")
        print("  • Processing payments")
        print(f"\n🌐 View dashboard: http://localhost:8080")
        print(f"🏪 View marketplace: http://localhost:8080/marketplace\n")
        sys.exit(0)
    else:
        print(f"{Fore.YELLOW}⚠ Some tests failed{Style.RESET_ALL}")
        print(f"\n💡 Troubleshooting:")
        print(f"  • Check if both marketplace and agent are running")
        print(f"  • Check logs for errors")
        print(f"  • Verify GPU is detected")
        print(f"  • Ensure wallets are properly configured\n")
        sys.exit(1)


if __name__ == "__main__":
    # Global variable for created job ID
    created_job_id = None
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

