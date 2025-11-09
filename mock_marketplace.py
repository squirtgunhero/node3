# mock_marketplace.py
"""
Mock Marketplace Server for Testing

This creates a simple marketplace API server that the agent can connect to
for testing and development purposes.

NOW WITH REAL PAYMENTS! 💰
The marketplace has its own wallet and sends real SOL to agents.
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import uvicorn
import json
import os
from pathlib import Path
from loguru import logger
import asyncio

# Import our payment module
import sys
sys.path.append(str(Path(__file__).parent))
from payment_module import PaymentModule

# Pydantic models for request validation
class AgentAcceptData(BaseModel):
    wallet_address: str

app = FastAPI(title="Mock node3 Marketplace")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store jobs and agents
available_jobs: Dict[str, Dict] = {}
accepted_jobs: Dict[str, Dict] = {}
registered_agents: Dict[str, Dict] = {}
test_job_templates: List[Dict] = []

# Payment system
marketplace_wallet: Optional[PaymentModule] = None
escrow_balance: float = 0.0  # Track escrowed funds
payment_history: List[Dict] = []  # Track all payments

def load_test_jobs():
    """Load test job templates from test_jobs.json"""
    global test_job_templates
    
    test_jobs_file = Path(__file__).parent / "test_jobs.json"
    
    if test_jobs_file.exists():
        try:
            with open(test_jobs_file, 'r') as f:
                data = json.load(f)
                test_job_templates = data.get("test_jobs", [])
                logger.info(f"Loaded {len(test_job_templates)} test job template(s) from {test_jobs_file}")
        except Exception as e:
            logger.warning(f"Failed to load test_jobs.json: {e}. Using default job.")
            test_job_templates = []
    else:
        logger.warning(f"test_jobs.json not found at {test_jobs_file}. Using default job.")
        test_job_templates = []
    
    # Add fallback default job if no templates loaded
    if not test_job_templates:
        test_job_templates = [{
            "job_type": "inference",
            "name": "Default Test Job",
            "docker_image": "python:3.11-slim",
            "gpu_memory_required": 0,
            "estimated_duration": 5,
            "reward": 0.00005,
            "command": ["python", "-c", "print('Hello from node3!'); import time; time.sleep(2); print('Job complete!')"],
            "environment": {},
            "timeout": 30,
            "requires_gpu": False
        }]

# Load test jobs on startup
load_test_jobs()

class JobRequest(BaseModel):
    gpu_model: str
    gpu_vendor: Optional[str] = None
    gpu_type: Optional[str] = None
    compute_framework: Optional[str] = None
    gpu_memory: int
    compute_capability: Optional[tuple] = None
    max_concurrent_jobs: int = 1

@app.get("/")
async def root():
    return {
        "message": "Mock node3 Marketplace API",
        "status": "running",
        "endpoints": {
            "get_jobs": "POST /api/jobs/available",
            "accept_job": "POST /api/jobs/{job_id}/accept",
            "complete_job": "POST /api/jobs/{job_id}/complete",
            "fail_job": "POST /api/jobs/{job_id}/fail"
        }
    }

@app.post("/api/jobs/available")
async def get_available_jobs(request: JobRequest):
    """Return available jobs matching GPU capabilities"""
    logger.info(f"Agent requesting jobs: {request.gpu_model} ({request.gpu_vendor})")
    
    # Add agent to registry
    agent_id = f"{request.gpu_vendor}_{request.gpu_model}"
    registered_agents[agent_id] = {
        "gpu_info": request.dict(),
        "last_seen": datetime.now().isoformat()
    }
    
    # Match jobs from templates based on capabilities
    jobs = []
    
    for template in test_job_templates:
        # Check if job requires GPU
        requires_gpu = template.get("requires_gpu", False)
        gpu_memory_required = template.get("gpu_memory_required", 0)
        
        # Match jobs:
        # 1. CPU-only jobs (no GPU required) - always available
        # 2. GPU jobs - only if agent has enough GPU memory
        if not requires_gpu or request.gpu_memory >= gpu_memory_required:
            # Create a new job instance with a unique job_id
            new_job = {
                "job_id": str(uuid.uuid4()),
                "job_type": template.get("job_type", "computation"),
                "docker_image": template.get("docker_image", "python:3.11-slim"),
                "gpu_memory_required": gpu_memory_required,
                "estimated_duration": template.get("estimated_duration", 60),
                "reward": template.get("reward", 0.001),
                "input_data_url": template.get("input_data_url", ""),
                "output_upload_url": template.get("output_upload_url", ""),
                "command": template.get("command", []),
                "environment": template.get("environment", {}),
                "timeout": template.get("timeout", 300)
            }
            
            jobs.append(new_job)
            available_jobs[new_job["job_id"]] = new_job.copy()
            logger.debug(f"Added job: {template.get('name', 'Unknown')} ({new_job['job_id'][:8]}...)")
    
    logger.info(f"Returning {len(jobs)} job(s) to agent")
    return {"jobs": jobs}

@app.post("/api/jobs/{job_id}/accept")
async def accept_job(job_id: str, agent_data: AgentAcceptData):
    """Agent accepts a job - must provide wallet address for payment"""
    if job_id not in available_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Extract wallet address from validated request body
    wallet_address = agent_data.wallet_address
    
    if not wallet_address:
        raise HTTPException(
            status_code=400, 
            detail="Agent wallet address required for payment"
        )
    
    job = available_jobs[job_id]
    accepted_jobs[job_id] = {
        **job,
        "accepted_at": datetime.now().isoformat(),
        "status": "accepted",
        "agent_wallet": wallet_address  # Store for payment later
    }
    
    logger.info(f"Job {job_id} accepted by agent {wallet_address}")
    return {
        "status": "accepted", 
        "job_id": job_id,
        "payment_address": wallet_address,
        "reward": job.get("reward", 0.001)
    }

@app.post("/api/jobs/{job_id}/complete")
async def complete_job(job_id: str, completion_data: dict):
    """Agent reports job completion - SENDS REAL SOL PAYMENT! 💰"""
    global escrow_balance, payment_history
    
    if job_id not in accepted_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = accepted_jobs[job_id]
    job["status"] = "completed"
    job["completed_at"] = datetime.now().isoformat()
    job["completion_data"] = completion_data
    
    logger.info(f"Job {job_id} completed successfully - processing payment...")
    
    # Send real SOL payment!
    if marketplace_wallet:
        agent_wallet = job.get("agent_wallet")
        reward = job.get("reward", 0.001)
        
        if agent_wallet:
            try:
                # Send payment
                signature = await marketplace_wallet.send_payment(
                    to_address=agent_wallet,
                    amount_sol=reward,
                    memo=f"Payment for job {job_id}"
                )
                
                if signature:
                    # Record payment
                    payment_record = {
                        'job_id': job_id,
                        'agent_wallet': agent_wallet,
                        'amount': reward,
                        'signature': signature,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'confirmed'
                    }
                    payment_history.append(payment_record)
                    job["payment_signature"] = signature
                    
                    # Update escrow
                    escrow_balance -= reward
                    
                    logger.info(f"💰 PAID {reward} SOL to {agent_wallet}")
                    logger.info(f"   Transaction: {signature}")
                    
                    return {
                        "status": "completed",
                        "message": f"Payment of {reward} SOL sent!",
                        "job_id": job_id,
                        "payment_signature": signature,
                        "amount_paid": reward
                    }
                else:
                    logger.error("Payment transaction failed")
                    return {
                        "status": "completed",
                        "message": "Job completed but payment failed - will retry",
                        "job_id": job_id
                    }
                    
            except Exception as e:
                logger.error(f"Error sending payment: {e}")
                return {
                    "status": "completed",
                    "message": f"Job completed but payment error: {str(e)}",
                    "job_id": job_id
                }
        else:
            logger.warning("No agent wallet address provided")
            return {
                "status": "completed",
                "message": "Job completed but no wallet address to pay",
                "job_id": job_id
            }
    else:
        logger.warning("Marketplace wallet not initialized - payment skipped")
        return {
            "status": "completed",
            "message": "Payment system not available",
            "job_id": job_id
        }

@app.post("/api/jobs/{job_id}/fail")
async def fail_job(job_id: str, failure_data: dict):
    """Agent reports job failure"""
    if job_id not in accepted_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    accepted_jobs[job_id]["status"] = "failed"
    accepted_jobs[job_id]["failed_at"] = datetime.now().isoformat()
    accepted_jobs[job_id]["failure_data"] = failure_data
    
    logger.warning(f"Job {job_id} failed: {failure_data.get('error_message', 'Unknown error')}")
    return {
        "status": "failed",
        "message": "Job failure recorded",
        "job_id": job_id
    }

@app.get("/api/status")
async def marketplace_status():
    """Get marketplace status"""
    return {
        "status": "running",
        "available_jobs": len(available_jobs),
        "accepted_jobs": len(accepted_jobs),
        "registered_agents": len(registered_agents),
        "agents": list(registered_agents.keys())
    }

@app.get("/api/jobs")
async def list_jobs():
    """List all jobs"""
    return {
        "available": list(available_jobs.values()),
        "accepted": list(accepted_jobs.values())
    }

@app.on_event("startup")
async def startup_event():
    """Initialize marketplace wallet on startup"""
    global marketplace_wallet, escrow_balance
    
    logger.info("Initializing marketplace payment system...")
    
    # Initialize marketplace wallet
    rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    wallet_path = "./marketplace_wallet.json"
    
    marketplace_wallet = PaymentModule(rpc_url=rpc_url, wallet_path=wallet_path)
    await marketplace_wallet.initialize()
    
    # Get initial balance
    balance = await marketplace_wallet.get_balance()
    escrow_balance = balance
    
    logger.info(f"💰 Marketplace Wallet: {marketplace_wallet.get_wallet_address()}")
    logger.info(f"💰 Balance: {balance} SOL")
    
    if balance < 0.1:
        logger.warning("⚠️  Marketplace wallet has low balance!")
        logger.warning("   To fund it on devnet:")
        logger.warning(f"   1. Visit: https://faucet.solana.com")
        logger.warning(f"   2. Enter: {marketplace_wallet.get_wallet_address()}")
        logger.warning("   3. Request 2 SOL (devnet only)")
        logger.warning("")
        logger.warning("   Or use the API: POST /api/marketplace/fund")
    else:
        logger.info(f"✅ Marketplace is funded and ready to pay agents!")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global marketplace_wallet
    if marketplace_wallet:
        await marketplace_wallet.close()

@app.get("/api/marketplace/info")
async def get_marketplace_info():
    """Get marketplace wallet and payment info"""
    if not marketplace_wallet:
        raise HTTPException(status_code=503, detail="Payment system not initialized")
    
    balance = await marketplace_wallet.get_balance()
    
    return {
        "wallet_address": marketplace_wallet.get_wallet_address(),
        "balance": balance,
        "escrow_balance": escrow_balance,
        "rpc_url": marketplace_wallet.rpc_url,
        "payments_processed": len(payment_history),
        "total_paid": sum(p['amount'] for p in payment_history)
    }

@app.post("/api/marketplace/fund")
async def fund_marketplace():
    """Request devnet SOL from faucet (devnet only!)"""
    if not marketplace_wallet:
        raise HTTPException(status_code=503, detail="Payment system not initialized")
    
    try:
        success = await marketplace_wallet.request_airdrop(amount_sol=2.0)
        
        if success:
            balance = await marketplace_wallet.get_balance()
            return {
                "status": "success",
                "message": "Marketplace funded with 2 SOL from devnet faucet",
                "new_balance": balance
            }
        else:
            raise HTTPException(status_code=500, detail="Airdrop failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payments/history")
async def get_payment_history():
    """Get all payment history"""
    return {
        "payments": payment_history,
        "total_payments": len(payment_history),
        "total_amount": sum(p['amount'] for p in payment_history)
    }

if __name__ == "__main__":
    logger.info("Starting Mock Marketplace Server with REAL PAYMENTS! 💰")
    logger.info("Marketplace will be available at: http://127.0.0.1:8000")
    logger.info("Agent should connect to: http://127.0.0.1:8000")
    logger.info("")
    logger.info("NEW FEATURES:")
    logger.info("  - Real Solana wallet for marketplace")
    logger.info("  - Sends real SOL to agents on job completion")
    logger.info("  - Track all payments on-chain")
    logger.info("")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

