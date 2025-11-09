#!/usr/bin/env python3
"""
Production node3 Marketplace Server
===================================

A production-ready marketplace API for distributing compute jobs to agents.

Features:
- PostgreSQL database for persistence
- Agent authentication via API keys
- Job queue management
- Payment processing with Solana
- Rate limiting and security
- Monitoring and logging
- Admin API

Requirements:
- PostgreSQL database
- Redis (optional, for caching)
- Solana wallet with funds
"""

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uuid
import uvicorn
import os
from pathlib import Path
from loguru import logger
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON, select
import hashlib
import secrets

# Import payment module and load balancer
from payment_module import PaymentModule
from load_balancer import LoadBalancer, JobPriority

# ============================================================================
# Configuration
# ============================================================================

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost/node3_marketplace")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
MARKETPLACE_WALLET_PATH = os.getenv("MARKETPLACE_WALLET_PATH", "./marketplace_wallet.json")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", secrets.token_urlsafe(32))
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
PORT = int(os.getenv("PORT", "8000"))

# ============================================================================
# Database Setup
# ============================================================================

Base = declarative_base()

# Database Models
class Agent(Base):
    """Registered agent with authentication"""
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key = Column(String, unique=True, nullable=False, index=True)
    wallet_address = Column(String, nullable=False)
    gpu_model = Column(String)
    gpu_vendor = Column(String)
    gpu_memory = Column(Integer)
    compute_capability = Column(JSON)
    
    # Stats
    total_jobs_completed = Column(Integer, default=0)
    total_jobs_failed = Column(Integer, default=0)
    total_earned = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    reputation_score = Column(Float, default=100.0)


class Job(Base):
    """Job in the marketplace"""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type = Column(String, nullable=False)
    docker_image = Column(String, nullable=False)
    command = Column(JSON)
    environment = Column(JSON)
    
    # Requirements
    gpu_memory_required = Column(Integer, default=0)
    requires_gpu = Column(Boolean, default=False)
    estimated_duration = Column(Integer)  # seconds
    timeout = Column(Integer)  # seconds
    
    # Data
    input_data_url = Column(String)
    output_upload_url = Column(String)
    
    # Payment
    reward = Column(Float, nullable=False)
    
    # Assignment
    agent_id = Column(String, nullable=True)
    agent_wallet = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="available")  # available, accepted, running, completed, failed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    completion_data = Column(JSON, nullable=True)
    failure_reason = Column(String, nullable=True)
    
    # Payment
    payment_signature = Column(String, nullable=True)


class Payment(Base):
    """Payment record"""
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    agent_wallet = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    signature = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="confirmed")  # pending, confirmed, failed


# Database engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Dependency for database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ============================================================================
# Authentication
# ============================================================================

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_agent(
    api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Agent:
    """Authenticate agent via API key"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Query agent by API key
    result = await db.execute(select(Agent).where(Agent.api_key == api_key))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not agent.is_active:
        raise HTTPException(status_code=403, detail="Agent account disabled")
    
    # Update last seen
    agent.last_seen = datetime.utcnow()
    await db.commit()
    
    return agent


async def get_admin(api_key: str = Depends(api_key_header)):
    """Authenticate admin via API key"""
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Admin access required")
    return True


# ============================================================================
# Pydantic Models (API)
# ============================================================================

class AgentRegisterRequest(BaseModel):
    wallet_address: str
    gpu_model: str
    gpu_vendor: str
    gpu_memory: int
    compute_capability: Optional[Dict] = None


class AgentRegisterResponse(BaseModel):
    agent_id: str
    api_key: str
    message: str


class JobRequest(BaseModel):
    gpu_model: str
    gpu_vendor: Optional[str] = None
    gpu_memory: int
    max_concurrent_jobs: int = 1


class JobResponse(BaseModel):
    job_id: str
    job_type: str
    docker_image: str
    command: List[str]
    environment: Dict
    gpu_memory_required: int
    estimated_duration: int
    reward: float
    timeout: int
    input_data_url: Optional[str] = None
    output_upload_url: Optional[str] = None


class JobAcceptRequest(BaseModel):
    wallet_address: str


class JobCompleteRequest(BaseModel):
    output_data: Optional[Dict] = None
    execution_time: Optional[float] = None
    metrics: Optional[Dict] = None


class JobFailRequest(BaseModel):
    error_message: str
    error_type: Optional[str] = None


class AdminJobCreateRequest(BaseModel):
    job_type: str
    docker_image: str
    command: List[str]
    environment: Dict = {}
    gpu_memory_required: int = 0
    requires_gpu: bool = False
    estimated_duration: int = 60
    timeout: int = 300
    reward: float = 0.001
    input_data_url: Optional[str] = None
    output_upload_url: Optional[str] = None


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="node3 Marketplace API",
    version="1.0.0",
    description="Production marketplace for distributing compute jobs to agents"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global modules
payment_module: Optional[PaymentModule] = None
load_balancer: Optional[LoadBalancer] = None


# ============================================================================
# Public Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API information"""
    return {
        "name": "node3 Marketplace API",
        "version": "1.0.0",
        "status": "running",
        "environment": ENVIRONMENT,
        "endpoints": {
            "register": "POST /api/agents/register",
            "jobs": "POST /api/jobs/available",
            "accept": "POST /api/jobs/{job_id}/accept",
            "complete": "POST /api/jobs/{job_id}/complete",
            "fail": "POST /api/jobs/{job_id}/fail"
        }
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database
        await db.execute(select(1))
        
        # Check payment system
        payment_status = "ok" if payment_module else "not_initialized"
        
        return {
            "status": "healthy",
            "database": "connected",
            "payment_system": payment_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/api/marketplace/agents")
async def list_marketplace_agents(db: AsyncSession = Depends(get_db)):
    """Public endpoint to list available compute agents"""
    try:
        # Query all active agents
        result = await db.execute(
            select(Agent).where(Agent.is_active == True)
        )
        agents = result.scalars().all()
        
        # Convert to response format
        agent_list = []
        for agent in agents:
            agent_list.append({
                'id': agent.id,
                'gpu_model': agent.gpu_model or 'Unknown',
                'gpu_vendor': agent.gpu_vendor or 'Unknown',
                'gpu_memory': agent.gpu_memory or 0,
                'compute_framework': agent.compute_capability.get('framework', 'Unknown') if agent.compute_capability else 'Unknown',
                'status': 'available' if agent.is_active else 'offline',
                'jobs_completed': agent.total_jobs_completed,
                'uptime': '99%',  # TODO: Track actual uptime
                'rate': 0.001,  # TODO: Make this configurable per agent
                'gpu_count': 1
            })
        
        return {'agents': agent_list}
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return {'agents': []}


# ============================================================================
# Agent Endpoints
# ============================================================================

@app.post("/api/agents/register", response_model=AgentRegisterResponse)
async def register_agent(
    request: AgentRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new agent and receive API key"""
    global load_balancer
    
    # Generate API key
    api_key = secrets.token_urlsafe(32)
    
    # Create agent
    agent = Agent(
        api_key=api_key,
        wallet_address=request.wallet_address,
        gpu_model=request.gpu_model,
        gpu_vendor=request.gpu_vendor,
        gpu_memory=request.gpu_memory,
        compute_capability=request.compute_capability
    )
    
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    
    # Register with load balancer
    if load_balancer:
        max_concurrent = 2  # TODO: Make configurable per agent
        load_balancer.register_agent(
            agent_id=agent.id,
            gpu_memory=request.gpu_memory,
            max_concurrent_jobs=max_concurrent
        )
    
    logger.info(f"Registered new agent: {agent.id} ({request.gpu_model})")
    
    return AgentRegisterResponse(
        agent_id=agent.id,
        api_key=api_key,
        message="Agent registered successfully. Save your API key!"
    )


@app.post("/api/jobs/available")
async def get_available_jobs(
    request: JobRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, List[JobResponse]]:
    """Get available jobs matching agent capabilities"""
    
    # Query available jobs
    query = select(Job).where(
        Job.status == "available"
    )
    
    # Filter by GPU memory if required
    if request.gpu_memory:
        query = query.where(Job.gpu_memory_required <= request.gpu_memory)
    
    result = await db.execute(query.limit(10))
    jobs = result.scalars().all()
    
    # Convert to response models
    job_responses = [
        JobResponse(
            job_id=job.id,
            job_type=job.job_type,
            docker_image=job.docker_image,
            command=job.command or [],
            environment=job.environment or {},
            gpu_memory_required=job.gpu_memory_required,
            estimated_duration=job.estimated_duration,
            reward=job.reward,
            timeout=job.timeout,
            input_data_url=job.input_data_url,
            output_upload_url=job.output_upload_url
        )
        for job in jobs
    ]
    
    logger.info(f"Agent {agent.id} requested jobs, returning {len(job_responses)}")
    
    return {"jobs": job_responses}


@app.post("/api/jobs/{job_id}/accept")
async def accept_job(
    job_id: str,
    request: JobAcceptRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Agent accepts a job"""
    
    # Get job
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "available":
        raise HTTPException(status_code=400, detail=f"Job not available (status: {job.status})")
    
    # Assign to agent
    job.status = "accepted"
    job.agent_id = agent.id
    job.agent_wallet = request.wallet_address
    job.accepted_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"Job {job_id} accepted by agent {agent.id}")
    
    return {
        "status": "accepted",
        "job_id": job_id,
        "reward": job.reward,
        "message": "Job accepted. Start execution."
    }


@app.post("/api/jobs/{job_id}/complete")
async def complete_job(
    job_id: str,
    request: JobCompleteRequest,
    background_tasks: BackgroundTasks,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Agent reports job completion - triggers payment"""
    global load_balancer
    
    # Get job
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.agent_id != agent.id:
        raise HTTPException(status_code=403, detail="Not your job")
    
    if job.status not in ["accepted", "running"]:
        raise HTTPException(status_code=400, detail=f"Invalid job status: {job.status}")
    
    # Calculate duration
    duration = request.execution_time or 60.0
    if job.started_at:
        duration = (datetime.utcnow() - job.started_at).total_seconds()
    
    # Update job
    job.status = "completed"
    job.completed_at = datetime.utcnow()
    job.completion_data = request.dict()
    
    # Update agent stats
    agent.total_jobs_completed += 1
    agent.total_earned += job.reward
    
    await db.commit()
    
    # Update load balancer
    if load_balancer:
        load_balancer.job_completed(
            job_id=job_id,
            agent_id=agent.id,
            duration=duration,
            success=True
        )
    
    logger.info(f"Job {job_id} completed by agent {agent.id} in {duration:.1f}s")
    
    # Process payment in background
    if payment_module and job.agent_wallet:
        background_tasks.add_task(
            process_payment,
            job_id=job_id,
            agent_id=agent.id,
            wallet_address=job.agent_wallet,
            amount=job.reward
        )
    
    return {
        "status": "completed",
        "job_id": job_id,
        "reward": job.reward,
        "message": "Job completed. Payment processing..."
    }


@app.post("/api/jobs/{job_id}/fail")
async def fail_job(
    job_id: str,
    request: JobFailRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Agent reports job failure"""
    global load_balancer
    
    # Get job
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.agent_id != agent.id:
        raise HTTPException(status_code=403, detail="Not your job")
    
    # Update job
    job.status = "failed"
    job.failure_reason = request.error_message
    job.completed_at = datetime.utcnow()
    
    # Update agent stats
    agent.total_jobs_failed += 1
    # Decrease reputation slightly
    agent.reputation_score = max(0, agent.reputation_score - 1.0)
    
    await db.commit()
    
    # Notify load balancer (will auto-retry if configured)
    if load_balancer:
        load_balancer.job_failed(
            job_id=job_id,
            agent_id=agent.id,
            retry=True  # Auto-retry failed jobs
        )
    
    logger.warning(f"Job {job_id} failed on agent {agent.id}: {request.error_message}")
    
    return {
        "status": "failed",
        "job_id": job_id,
        "message": "Job failure recorded"
    }


@app.post("/api/agents/heartbeat")
async def agent_heartbeat(agent: Agent = Depends(get_current_agent)):
    """Agent sends heartbeat to indicate it's still alive"""
    global load_balancer
    
    # Update agent last seen
    agent.last_seen = datetime.utcnow()
    
    # Update load balancer
    if load_balancer:
        load_balancer.heartbeat(agent.id)
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.post("/api/admin/jobs/create")
async def create_job(
    request: AdminJobCreateRequest,
    admin: bool = Depends(get_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Create a new job"""
    global load_balancer
    
    job = Job(
        job_type=request.job_type,
        docker_image=request.docker_image,
        command=request.command,
        environment=request.environment,
        gpu_memory_required=request.gpu_memory_required,
        requires_gpu=request.requires_gpu,
        estimated_duration=request.estimated_duration,
        timeout=request.timeout,
        reward=request.reward,
        input_data_url=request.input_data_url,
        output_upload_url=request.output_upload_url
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Add to load balancer queue
    if load_balancer:
        # Determine priority based on reward (simple heuristic)
        if request.reward >= 0.01:
            priority = JobPriority.HIGH
        elif request.reward >= 0.001:
            priority = JobPriority.NORMAL
        else:
            priority = JobPriority.LOW
        
        load_balancer.enqueue_job(
            job_id=job.id,
            gpu_memory_required=request.gpu_memory_required,
            estimated_duration=request.estimated_duration,
            timeout=request.timeout,
            priority=priority
        )
    
    logger.info(f"Admin created job: {job.id}")
    
    return {"job_id": job.id, "status": "created"}


@app.get("/api/admin/stats")
async def get_stats(
    admin: bool = Depends(get_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get marketplace statistics"""
    global load_balancer
    
    # Count agents
    agents_result = await db.execute(select(Agent))
    total_agents = len(agents_result.scalars().all())
    
    # Count jobs by status
    jobs_result = await db.execute(select(Job))
    all_jobs = jobs_result.scalars().all()
    
    jobs_by_status = {}
    for job in all_jobs:
        jobs_by_status[job.status] = jobs_by_status.get(job.status, 0) + 1
    
    # Count payments
    payments_result = await db.execute(select(Payment))
    all_payments = payments_result.scalars().all()
    total_paid = sum(p.amount for p in all_payments)
    
    # Get load balancer stats
    lb_stats = load_balancer.get_stats() if load_balancer else {}
    
    return {
        "agents": {
            "total": total_agents
        },
        "jobs": {
            "total": len(all_jobs),
            "by_status": jobs_by_status
        },
        "payments": {
            "total_count": len(all_payments),
            "total_amount": total_paid
        },
        "load_balancer": lb_stats
    }


@app.get("/api/admin/load-balancer")
async def get_load_balancer_stats(admin: bool = Depends(get_admin)):
    """Admin: Get detailed load balancer statistics"""
    global load_balancer
    
    if not load_balancer:
        raise HTTPException(status_code=503, detail="Load balancer not initialized")
    
    return load_balancer.get_stats()


# ============================================================================
# Background Tasks
# ============================================================================

async def process_payment(job_id: str, agent_id: str, wallet_address: str, amount: float):
    """Process payment to agent (background task)"""
    global payment_module
    
    if not payment_module:
        logger.error("Payment module not initialized")
        return
    
    try:
        # Send payment
        signature = await payment_module.send_payment(
            to_address=wallet_address,
            amount_sol=amount,
            memo=f"Payment for job {job_id}"
        )
        
        if signature:
            # Record payment
            async with AsyncSessionLocal() as db:
                payment = Payment(
                    job_id=job_id,
                    agent_id=agent_id,
                    agent_wallet=wallet_address,
                    amount=amount,
                    signature=signature,
                    status="confirmed"
                )
                db.add(payment)
                
                # Update job with signature
                result = await db.execute(select(Job).where(Job.id == job_id))
                job = result.scalar_one_or_none()
                if job:
                    job.payment_signature = signature
                
                await db.commit()
            
            logger.info(f"💰 Paid {amount} SOL to {wallet_address} (job: {job_id})")
        else:
            logger.error(f"Payment failed for job {job_id}")
            
    except Exception as e:
        logger.error(f"Error processing payment: {e}")


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global payment_module, load_balancer
    
    logger.info("=" * 60)
    logger.info("Starting node3 Production Marketplace")
    logger.info("=" * 60)
    
    # Create database tables
    logger.info("Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✓ Database ready")
    
    # Initialize load balancer
    logger.info("Initializing load balancer...")
    load_balancer = LoadBalancer(
        heartbeat_timeout=60,
        job_timeout_buffer=1.2,
        rebalance_interval=30
    )
    logger.info("✓ Load balancer ready")
    
    # Start load balancer maintenance task
    asyncio.create_task(load_balancer.run_maintenance())
    logger.info("✓ Load balancer maintenance task started")
    
    # Initialize payment system
    logger.info("Initializing payment system...")
    payment_module = PaymentModule(
        rpc_url=SOLANA_RPC_URL,
        wallet_path=MARKETPLACE_WALLET_PATH
    )
    await payment_module.initialize()
    
    balance = await payment_module.get_balance()
    wallet_address = payment_module.get_wallet_address()
    
    logger.info(f"💰 Marketplace Wallet: {wallet_address}")
    logger.info(f"💰 Balance: {balance} SOL")
    
    if balance < 1.0:
        logger.warning("⚠️  Low marketplace balance! Fund wallet to pay agents.")
    
    # Log admin API key (only in development)
    if ENVIRONMENT == "development":
        logger.info(f"🔑 Admin API Key: {ADMIN_API_KEY}")
    
    logger.info("=" * 60)
    logger.info("✓ Marketplace is running and ready!")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global payment_module
    
    logger.info("Shutting down marketplace...")
    
    if payment_module:
        await payment_module.close()
    
    logger.info("✓ Marketplace stopped")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    logger.info(f"Starting on port {PORT}...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )

