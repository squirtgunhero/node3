# Load Balancing & Job Reliability 🔄

## Overview

The node³ marketplace implements a sophisticated load balancing system to ensure **zero job drop-offs** and optimal resource utilization across all GPU agents.

## Key Features

### 1. **Intelligent Job Queueing**
- Priority-based job queue (LOW, NORMAL, HIGH, URGENT)
- Automatic job assignment to best-suited agents
- Fair distribution algorithm

### 2. **Agent Capacity Tracking**
- Real-time monitoring of agent workload
- GPU memory matching
- Concurrent job limits per agent

### 3. **Failure Recovery**
- Automatic retry for failed jobs (up to 3 attempts)
- Job timeout detection and reassignment
- Agent health monitoring

### 4. **Health Monitoring**
- Agent heartbeat system (every 30 seconds)
- Unhealthy agent detection (60s timeout)
- Automatic job reassignment from dead agents

### 5. **Load Distribution**
- Agent scoring based on:
  - Available capacity (50% weight)
  - Success rate (30% weight)
  - Average completion speed (20% weight)
- Best agent selected for each job

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐        ┌──────────────┐              │
│  │  Job Queue   │        │ Agent Pool   │              │
│  │              │        │              │              │
│  │ • Priority   │◄──────►│ • Capacity   │              │
│  │ • Timeout    │        │ • Health     │              │
│  │ • Retry      │        │ • Score      │              │
│  └──────────────┘        └──────────────┘              │
│                                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │        Maintenance Loop (30s)                     │  │
│  │  • Check timeouts                                 │  │
│  │  • Check agent health                             │  │
│  │  • Assign queued jobs                             │  │
│  │  • Update statistics                              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## How It Prevents Drop-offs

### Problem 1: Agent Overload
**Without Load Balancing:**
- Jobs assigned without checking agent capacity
- Agents get overloaded and crash
- Jobs fail without retry

**With Load Balancing:**
```python
# Each agent has a capacity limit
max_concurrent_jobs = 2  # Configurable

# Only assign if agent has available slots
if agent.available_slots > 0:
    assign_job(job, agent)
```

### Problem 2: Job Timeout
**Without Load Balancing:**
- Jobs run indefinitely
- No timeout enforcement
- Resources wasted

**With Load Balancing:**
```python
# Monitor job execution time
timeout = job.timeout * 1.2  # 20% buffer
if elapsed_time > timeout:
    # Automatically reassign to another agent
    reassign_job(job)
```

### Problem 3: Agent Failure
**Without Load Balancing:**
- Agent crashes silently
- Jobs lost forever

**With Load Balancing:**
```python
# Agent heartbeat every 30s
async def agent_loop():
    while running:
        send_heartbeat()
        await asyncio.sleep(30)

# Marketplace checks heartbeats
if last_heartbeat > 60_seconds_ago:
    # Mark agent unhealthy
    # Reassign all its jobs
    for job in agent.jobs:
        reassign_job(job)
```

### Problem 4: Failed Jobs
**Without Load Balancing:**
- Job fails once and is lost

**With Load Balancing:**
```python
# Automatic retry with priority boost
if job.failed and job.retry_count < 3:
    job.retry_count += 1
    job.priority = increase_priority(job.priority)
    re_queue(job)  # Try again on different agent
```

## Job Lifecycle with Load Balancing

```
1. Job Created
   └─> Added to priority queue
       └─> Priority: LOW | NORMAL | HIGH | URGENT

2. Assignment Phase (every 30s)
   └─> Load balancer selects best agent
       ├─> Check GPU memory match
       ├─> Check available capacity
       ├─> Calculate agent score
       └─> Assign to highest-scoring agent

3. Execution
   ├─> Agent sends heartbeat (30s intervals)
   ├─> Load balancer monitors timeout
   └─> If timeout: reassign to new agent

4. Completion/Failure
   ├─> Success: update agent stats, clear slot
   └─> Failure: auto-retry (up to 3x)
       └─> Priority increased for each retry
```

## Agent Scoring Algorithm

Agents are scored to find the best match for each job:

```python
def calculate_score(agent):
    # Availability: Can agent take more work?
    availability = agent.available_slots / agent.max_slots  # 50% weight
    
    # Reliability: Does agent complete jobs successfully?
    success_rate = agent.completed / (agent.completed + agent.failed)  # 30% weight
    
    # Speed: How fast does agent complete jobs?
    speed = 60 / max(1, agent.avg_completion_time)  # 20% weight
    
    return (availability * 0.5 + 
            success_rate * 0.3 + 
            speed * 0.2)
```

**Higher score = Better agent for the job**

## Configuration

### Load Balancer Settings

```python
LoadBalancer(
    heartbeat_timeout=60,        # Mark agent unhealthy after 60s
    job_timeout_buffer=1.2,      # Job timeout = timeout * 1.2
    rebalance_interval=30        # Check health/assign jobs every 30s
)
```

### Agent Settings

```python
# Per-agent concurrent job limit
max_concurrent_jobs = 2  # Can run 2 jobs simultaneously

# Job retry settings
max_retries = 3  # Try up to 3 times before giving up
```

### Priority Levels

```python
class JobPriority(Enum):
    LOW = 0      # Low priority jobs (e.g., batch processing)
    NORMAL = 1   # Regular jobs
    HIGH = 2     # Important jobs (higher reward)
    URGENT = 3   # Critical jobs (retried jobs)
```

## Monitoring

### Load Balancer Statistics

```bash
# Get detailed load balancer stats
curl http://localhost:8000/api/admin/load-balancer

# Response:
{
  "total_agents": 5,
  "healthy_agents": 5,
  "total_capacity": 10,
  "current_load": 7,
  "utilization": 70.0,
  "queued_jobs": 3,
  "assigned_jobs": 7,
  "total_jobs_queued": 1043,
  "total_jobs_assigned": 1040,
  "total_jobs_failed": 15,
  "total_jobs_retried": 12,
  "agents": [
    {
      "agent_id": "agent_123",
      "current_jobs": 2,
      "max_jobs": 2,
      "load_percent": 100.0,
      "total_completed": 156,
      "total_failed": 3,
      "success_rate": 98.1,
      "avg_time": 45.3,
      "score": 0.87,
      "is_healthy": true
    }
  ]
}
```

### Key Metrics

| Metric | Description | Good Value |
|--------|-------------|------------|
| Utilization | % of capacity in use | 60-80% |
| Success Rate | % of jobs completed | >95% |
| Queued Jobs | Jobs waiting | <10 |
| Healthy Agents | Agents responding | 100% |
| Retries | Failed jobs retried | Low |

## Example Scenarios

### Scenario 1: Agent Goes Offline

```
Time: 10:00:00 - Agent A assigned job_123
Time: 10:00:30 - Agent A sends heartbeat ✓
Time: 10:01:00 - Agent A sends heartbeat ✓
Time: 10:01:05 - Agent A CRASHES 💥
Time: 10:01:30 - No heartbeat from Agent A ❌
Time: 10:02:00 - No heartbeat from Agent A ❌
Time: 10:02:05 - Load balancer marks Agent A unhealthy
Time: 10:02:06 - job_123 reassigned to Agent B
Time: 10:03:00 - job_123 completed by Agent B ✓
```

**Result: Zero job drop-off despite agent crash**

### Scenario 2: Job Times Out

```
Time: 11:00:00 - Job assigned (timeout: 120s)
Time: 11:02:00 - Job should be done
Time: 11:02:24 - Job times out (120s * 1.2 = 144s)
Time: 11:02:25 - Load balancer reassigns job
Time: 11:02:30 - New agent starts job
Time: 11:04:00 - Job completed ✓
```

**Result: Stuck jobs automatically recovered**

### Scenario 3: Job Fails

```
Attempt 1:
  Time: 12:00:00 - job_456 assigned to Agent C
  Time: 12:00:30 - Agent C reports failure
  Time: 12:00:31 - Load balancer retries (attempt 1/3)
  Time: 12:00:31 - Priority: NORMAL → HIGH

Attempt 2:
  Time: 12:00:35 - job_456 assigned to Agent D
  Time: 12:01:00 - Agent D reports failure
  Time: 12:01:01 - Load balancer retries (attempt 2/3)
  Time: 12:01:01 - Priority: HIGH → URGENT

Attempt 3:
  Time: 12:01:05 - job_456 assigned to Agent E
  Time: 12:02:00 - Agent E completes successfully ✓
```

**Result: Transient failures automatically recovered**

## Best Practices

### For Marketplace Operators

1. **Monitor utilization** - Keep at 60-80% for optimal performance
2. **Scale capacity** - Add agents when utilization > 85%
3. **Check health** - Investigate agents with <95% success rate
4. **Review retries** - High retry rate indicates systemic issues

### For Agent Operators

1. **Stable connection** - Ensure reliable network connectivity
2. **Resource monitoring** - Monitor GPU memory and utilization
3. **Heartbeat health** - Verify heartbeats are being sent
4. **Handle failures** - Report failures with descriptive error messages

### For Job Posters

1. **Accurate timeouts** - Set realistic timeout values
2. **Priority usage** - Use HIGH priority only when necessary
3. **Resource requirements** - Specify GPU memory accurately
4. **Retry tolerance** - Design jobs to be idempotent

## Troubleshooting

### High Queue Length

**Problem:** Jobs not getting assigned fast enough

**Diagnosis:**
```bash
curl http://localhost:8000/api/admin/load-balancer | jq '.queued_jobs'
```

**Solutions:**
- Add more agents
- Increase `max_concurrent_jobs` per agent
- Check if jobs have unrealistic GPU requirements

### Low Success Rate

**Problem:** Many jobs failing

**Diagnosis:**
```bash
curl http://localhost:8000/api/admin/load-balancer | jq '.agents[] | select(.success_rate < 95)'
```

**Solutions:**
- Investigate specific failing agents
- Check job timeout settings
- Review job resource requirements

### Unhealthy Agents

**Problem:** Agents going offline

**Diagnosis:**
```bash
curl http://localhost:8000/api/admin/load-balancer | jq '.agents[] | select(.is_healthy == false)'
```

**Solutions:**
- Check agent logs
- Verify network connectivity
- Restart affected agents
- Adjust heartbeat_timeout if network is slow

## Performance Impact

### Load Balancer Overhead

- **Memory:** ~1 MB per 1000 jobs + ~10 KB per agent
- **CPU:** <1% (maintenance runs every 30s)
- **Network:** Minimal (heartbeats only)

### Latency Impact

- **Job Assignment:** <100ms (scoring + queue operations)
- **Heartbeat:** <50ms (lightweight POST request)
- **Timeout Check:** <10ms per job

## Future Enhancements

Planned improvements:

1. **Predictive Scaling**
   - ML-based load prediction
   - Auto-scale agent requests

2. **Geographic Distribution**
   - Prefer agents closer to data
   - Reduce network latency

3. **Cost Optimization**
   - Prefer cheaper agents when performance similar
   - Batch similar jobs

4. **Advanced Scheduling**
   - Job dependencies
   - Deadline scheduling
   - Resource reservations

---

## Summary

The load balancing system ensures:

✅ **Zero job drop-offs** through automatic retry  
✅ **High availability** via health monitoring  
✅ **Optimal performance** with intelligent assignment  
✅ **Fault tolerance** through redundancy  
✅ **Fair distribution** across all agents  

**Your jobs are safe, your agents are protected, and your marketplace runs smoothly!** 🎯

