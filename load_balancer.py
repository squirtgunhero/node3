#!/usr/bin/env python3
"""
Load Balancer for node³ Marketplace
====================================

Handles:
- Agent capacity tracking
- Job queue management
- Fair job distribution
- Failure recovery
- Health monitoring
- Auto-retry for failed jobs

Features:
- Prevents agent overload
- Ensures no job drop-offs
- Automatic failover
- Priority queuing
- Agent scoring
"""

import asyncio
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
import heapq
from collections import defaultdict


class JobPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class AgentCapacity:
    """Track agent capacity and load"""
    agent_id: str
    gpu_memory: int
    max_concurrent_jobs: int
    current_jobs: int = 0
    total_completed: int = 0
    total_failed: int = 0
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    average_completion_time: float = 60.0  # seconds
    success_rate: float = 1.0
    is_healthy: bool = True
    
    @property
    def available_slots(self) -> int:
        """Number of jobs this agent can accept"""
        return max(0, self.max_concurrent_jobs - self.current_jobs)
    
    @property
    def load_percentage(self) -> float:
        """Current load as percentage"""
        if self.max_concurrent_jobs == 0:
            return 100.0
        return (self.current_jobs / self.max_concurrent_jobs) * 100
    
    @property
    def score(self) -> float:
        """Agent score for load balancing (higher is better)"""
        # Factors: availability, success rate, completion time
        availability_score = self.available_slots / max(1, self.max_concurrent_jobs)
        success_score = self.success_rate
        speed_score = min(1.0, 60.0 / max(1.0, self.average_completion_time))
        
        return (availability_score * 0.5 + 
                success_score * 0.3 + 
                speed_score * 0.2)


@dataclass
class QueuedJob:
    """Job waiting in queue"""
    job_id: str
    priority: JobPriority
    gpu_memory_required: int
    estimated_duration: int
    timeout: int
    created_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    assigned_agent: Optional[str] = None
    assignment_time: Optional[datetime] = None
    
    def __lt__(self, other):
        """For priority queue ordering"""
        # Higher priority jobs first, then older jobs
        if self.priority != other.priority:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at


class LoadBalancer:
    """Intelligent load balancer for marketplace jobs"""
    
    def __init__(self, 
                 heartbeat_timeout: int = 60,
                 job_timeout_buffer: float = 1.2,
                 rebalance_interval: int = 30):
        self.agents: Dict[str, AgentCapacity] = {}
        self.job_queue: List[QueuedJob] = []  # Priority queue
        self.assigned_jobs: Dict[str, QueuedJob] = {}  # job_id -> QueuedJob
        self.agent_assignments: Dict[str, Set[str]] = defaultdict(set)  # agent_id -> job_ids
        
        self.heartbeat_timeout = heartbeat_timeout
        self.job_timeout_buffer = job_timeout_buffer
        self.rebalance_interval = rebalance_interval
        
        # Statistics
        self.total_jobs_queued = 0
        self.total_jobs_assigned = 0
        self.total_jobs_failed = 0
        self.total_jobs_retried = 0
        
    def register_agent(self, 
                      agent_id: str, 
                      gpu_memory: int,
                      max_concurrent_jobs: int = 1):
        """Register or update agent capacity"""
        if agent_id in self.agents:
            # Update existing agent
            agent = self.agents[agent_id]
            agent.gpu_memory = gpu_memory
            agent.max_concurrent_jobs = max_concurrent_jobs
            agent.last_heartbeat = datetime.utcnow()
            agent.is_healthy = True
            logger.info(f"Updated agent {agent_id}: {max_concurrent_jobs} slots, {gpu_memory/1e9:.1f}GB GPU")
        else:
            # New agent
            self.agents[agent_id] = AgentCapacity(
                agent_id=agent_id,
                gpu_memory=gpu_memory,
                max_concurrent_jobs=max_concurrent_jobs
            )
            logger.info(f"Registered new agent {agent_id}: {max_concurrent_jobs} slots, {gpu_memory/1e9:.1f}GB GPU")
    
    def heartbeat(self, agent_id: str):
        """Update agent heartbeat"""
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = datetime.utcnow()
            self.agents[agent_id].is_healthy = True
    
    def enqueue_job(self, 
                   job_id: str,
                   gpu_memory_required: int,
                   estimated_duration: int,
                   timeout: int,
                   priority: JobPriority = JobPriority.NORMAL) -> bool:
        """Add job to queue"""
        
        # Check if job already queued or assigned
        if job_id in self.assigned_jobs:
            logger.warning(f"Job {job_id} already assigned")
            return False
        
        if any(j.job_id == job_id for j in self.job_queue):
            logger.warning(f"Job {job_id} already in queue")
            return False
        
        job = QueuedJob(
            job_id=job_id,
            priority=priority,
            gpu_memory_required=gpu_memory_required,
            estimated_duration=estimated_duration,
            timeout=timeout,
            created_at=datetime.utcnow()
        )
        
        heapq.heappush(self.job_queue, job)
        self.total_jobs_queued += 1
        
        logger.info(f"Queued job {job_id} (priority: {priority.name}, GPU: {gpu_memory_required/1e9:.1f}GB)")
        return True
    
    def assign_jobs(self) -> List[tuple]:
        """Assign queued jobs to available agents
        
        Returns:
            List of (job_id, agent_id) tuples
        """
        assignments = []
        
        # Get healthy agents sorted by score (best first)
        available_agents = [
            agent for agent in self.agents.values()
            if agent.is_healthy and agent.available_slots > 0
        ]
        available_agents.sort(key=lambda a: a.score, reverse=True)
        
        if not available_agents:
            if self.job_queue:
                logger.warning(f"No available agents for {len(self.job_queue)} queued jobs")
            return assignments
        
        # Try to assign jobs
        temp_queue = []
        while self.job_queue:
            job = heapq.heappop(self.job_queue)
            
            # Find suitable agent
            assigned = False
            for agent in available_agents:
                # Check if agent can handle this job
                if (agent.available_slots > 0 and 
                    agent.gpu_memory >= job.gpu_memory_required):
                    
                    # Assign job to agent
                    job.assigned_agent = agent.agent_id
                    job.assignment_time = datetime.utcnow()
                    
                    self.assigned_jobs[job.job_id] = job
                    self.agent_assignments[agent.agent_id].add(job.job_id)
                    
                    agent.current_jobs += 1
                    self.total_jobs_assigned += 1
                    
                    assignments.append((job.job_id, agent.agent_id))
                    assigned = True
                    
                    logger.info(f"Assigned job {job.job_id} to agent {agent.agent_id} "
                              f"(load: {agent.load_percentage:.1f}%)")
                    break
            
            # If couldn't assign, put back in queue
            if not assigned:
                temp_queue.append(job)
        
        # Restore unassigned jobs to queue
        for job in temp_queue:
            heapq.heappush(self.job_queue, job)
        
        return assignments
    
    def job_completed(self, 
                     job_id: str, 
                     agent_id: str,
                     duration: float,
                     success: bool = True):
        """Mark job as completed"""
        
        # Update agent stats
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.current_jobs = max(0, agent.current_jobs - 1)
            
            if success:
                agent.total_completed += 1
                # Update average completion time (exponential moving average)
                alpha = 0.3
                agent.average_completion_time = (
                    alpha * duration + 
                    (1 - alpha) * agent.average_completion_time
                )
            else:
                agent.total_failed += 1
            
            # Update success rate
            total = agent.total_completed + agent.total_failed
            if total > 0:
                agent.success_rate = agent.total_completed / total
        
        # Remove from tracking
        if job_id in self.assigned_jobs:
            del self.assigned_jobs[job_id]
        
        if agent_id in self.agent_assignments:
            self.agent_assignments[agent_id].discard(job_id)
        
        if success:
            logger.info(f"Job {job_id} completed by {agent_id} in {duration:.1f}s")
        else:
            logger.warning(f"Job {job_id} failed on {agent_id}")
            self.total_jobs_failed += 1
    
    def job_failed(self, job_id: str, agent_id: str, retry: bool = True):
        """Handle job failure with optional retry"""
        
        # Mark as failed
        self.job_completed(job_id, agent_id, 0, success=False)
        
        # Retry logic
        if retry and job_id in self.assigned_jobs:
            job = self.assigned_jobs[job_id]
            
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.assigned_agent = None
                job.assignment_time = None
                
                # Re-queue with higher priority
                if job.priority.value < JobPriority.URGENT.value:
                    job.priority = JobPriority(job.priority.value + 1)
                
                heapq.heappush(self.job_queue, job)
                self.total_jobs_retried += 1
                
                logger.warning(f"Retrying job {job_id} (attempt {job.retry_count}/{job.max_retries})")
                return True
            else:
                logger.error(f"Job {job_id} failed after {job.max_retries} retries")
                return False
        
        return False
    
    def check_timeouts(self) -> List[str]:
        """Check for timed out jobs and reassign
        
        Returns:
            List of job_ids that timed out
        """
        timed_out = []
        now = datetime.utcnow()
        
        for job_id, job in list(self.assigned_jobs.items()):
            if job.assignment_time:
                elapsed = (now - job.assignment_time).total_seconds()
                timeout = job.timeout * self.job_timeout_buffer
                
                if elapsed > timeout:
                    logger.warning(f"Job {job_id} timed out on agent {job.assigned_agent} "
                                 f"({elapsed:.0f}s > {timeout:.0f}s)")
                    
                    timed_out.append(job_id)
                    
                    # Fail and retry
                    self.job_failed(job_id, job.assigned_agent, retry=True)
        
        return timed_out
    
    def check_agent_health(self) -> List[str]:
        """Check agent health and mark unhealthy agents
        
        Returns:
            List of unhealthy agent_ids
        """
        unhealthy = []
        now = datetime.utcnow()
        timeout = timedelta(seconds=self.heartbeat_timeout)
        
        for agent_id, agent in self.agents.items():
            if now - agent.last_heartbeat > timeout:
                if agent.is_healthy:
                    agent.is_healthy = False
                    logger.warning(f"Agent {agent_id} is unhealthy (no heartbeat for {self.heartbeat_timeout}s)")
                    unhealthy.append(agent_id)
                    
                    # Reassign jobs from unhealthy agent
                    for job_id in list(self.agent_assignments.get(agent_id, [])):
                        logger.warning(f"Reassigning job {job_id} from unhealthy agent {agent_id}")
                        self.job_failed(job_id, agent_id, retry=True)
        
        return unhealthy
    
    def get_stats(self) -> Dict:
        """Get load balancer statistics"""
        healthy_agents = sum(1 for a in self.agents.values() if a.is_healthy)
        total_capacity = sum(a.max_concurrent_jobs for a in self.agents.values() if a.is_healthy)
        current_load = sum(a.current_jobs for a in self.agents.values() if a.is_healthy)
        
        return {
            'total_agents': len(self.agents),
            'healthy_agents': healthy_agents,
            'total_capacity': total_capacity,
            'current_load': current_load,
            'utilization': (current_load / max(1, total_capacity)) * 100,
            'queued_jobs': len(self.job_queue),
            'assigned_jobs': len(self.assigned_jobs),
            'total_jobs_queued': self.total_jobs_queued,
            'total_jobs_assigned': self.total_jobs_assigned,
            'total_jobs_failed': self.total_jobs_failed,
            'total_jobs_retried': self.total_jobs_retried,
            'agents': [
                {
                    'agent_id': a.agent_id,
                    'current_jobs': a.current_jobs,
                    'max_jobs': a.max_concurrent_jobs,
                    'load_percent': a.load_percentage,
                    'total_completed': a.total_completed,
                    'total_failed': a.total_failed,
                    'success_rate': a.success_rate * 100,
                    'avg_time': a.average_completion_time,
                    'score': a.score,
                    'is_healthy': a.is_healthy
                }
                for a in sorted(self.agents.values(), 
                              key=lambda x: x.score, reverse=True)
            ]
        }
    
    async def run_maintenance(self):
        """Background task for maintenance"""
        logger.info("Load balancer maintenance started")
        
        while True:
            try:
                # Check for timed out jobs
                timed_out = self.check_timeouts()
                if timed_out:
                    logger.warning(f"Found {len(timed_out)} timed out jobs")
                
                # Check agent health
                unhealthy = self.check_agent_health()
                if unhealthy:
                    logger.warning(f"Found {len(unhealthy)} unhealthy agents")
                
                # Try to assign queued jobs
                if self.job_queue:
                    assignments = self.assign_jobs()
                    if assignments:
                        logger.info(f"Assigned {len(assignments)} jobs to agents")
                
                # Log stats
                stats = self.get_stats()
                logger.info(f"Load balancer: {stats['healthy_agents']}/{stats['total_agents']} agents, "
                          f"{stats['current_load']}/{stats['total_capacity']} jobs "
                          f"({stats['utilization']:.1f}% util), "
                          f"{stats['queued_jobs']} queued")
                
            except Exception as e:
                logger.error(f"Error in load balancer maintenance: {e}")
            
            await asyncio.sleep(self.rebalance_interval)


# Example usage
if __name__ == "__main__":
    import sys
    from loguru import logger
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    async def test_load_balancer():
        """Test the load balancer"""
        lb = LoadBalancer()
        
        # Register agents
        lb.register_agent("agent_1", gpu_memory=8*1e9, max_concurrent_jobs=2)
        lb.register_agent("agent_2", gpu_memory=24*1e9, max_concurrent_jobs=3)
        lb.register_agent("agent_3", gpu_memory=16*1e9, max_concurrent_jobs=1)
        
        # Queue jobs
        for i in range(10):
            priority = JobPriority.HIGH if i < 3 else JobPriority.NORMAL
            lb.enqueue_job(
                job_id=f"job_{i}",
                gpu_memory_required=8*1e9,
                estimated_duration=60,
                timeout=120,
                priority=priority
            )
        
        # Assign jobs
        assignments = lb.assign_jobs()
        print(f"\n✓ Assigned {len(assignments)} jobs")
        
        # Show stats
        stats = lb.get_stats()
        print(f"\n📊 Stats:")
        print(f"  Agents: {stats['healthy_agents']}/{stats['total_agents']}")
        print(f"  Load: {stats['current_load']}/{stats['total_capacity']} ({stats['utilization']:.1f}%)")
        print(f"  Queued: {stats['queued_jobs']}")
        print(f"\n📈 Agent Details:")
        for agent in stats['agents']:
            print(f"  {agent['agent_id']}: {agent['current_jobs']}/{agent['max_jobs']} jobs "
                  f"({agent['load_percent']:.1f}% load, score: {agent['score']:.2f})")
        
        # Simulate job completion
        if assignments:
            job_id, agent_id = assignments[0]
            lb.job_completed(job_id, agent_id, duration=45.0, success=True)
            print(f"\n✓ Completed job {job_id}")
        
        # Final stats
        stats = lb.get_stats()
        print(f"\n📊 Final Stats:")
        print(f"  Load: {stats['current_load']}/{stats['total_capacity']} ({stats['utilization']:.1f}%)")
        print(f"  Queued: {stats['queued_jobs']}")
    
    asyncio.run(test_load_balancer())

