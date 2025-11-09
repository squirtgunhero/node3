#!/usr/bin/env python3
"""
Test Dashboard UI
=================
Simple server to test the marketplace dashboard UI without running the full agent.
This serves the dashboard with mock data so you can see the UI in action.
"""

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path
import asyncio
import random
from datetime import datetime, timedelta

app = FastAPI(title="node3 Dashboard Test")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Mock data
mock_jobs = []
mock_wallet_address = "9xQeWvG8Z3wqKvBvZzKkLDvK6Rh4z3qKvBvZzKkLDvK"
mock_balance = 0.1234

# Generate some mock job history
def generate_mock_jobs():
    global mock_jobs
    job_types = ["inference", "training", "computation", "rendering"]
    statuses = ["completed", "failed", "pending", "running"]
    
    for i in range(15):
        created_at = datetime.now() - timedelta(hours=random.randint(1, 48))
        mock_jobs.append({
            "job_id": f"job_{i:04d}_{''.join(random.choices('abcdef0123456789', k=8))}",
            "job_type": random.choice(job_types),
            "status": random.choice(statuses),
            "reward": round(random.uniform(0.0001, 0.001), 6),
            "duration": random.randint(5, 300),
            "completed_at": created_at.isoformat()
        })

generate_mock_jobs()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the dashboard UI"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/marketplace", response_class=HTMLResponse)
async def marketplace(request: Request):
    """Serve the marketplace browsing UI"""
    return templates.TemplateResponse("marketplace.html", {"request": request})

@app.get("/api/status")
async def get_status():
    """Mock status endpoint"""
    return {
        'gpus': [
            {
                'index': 0,
                'name': 'NVIDIA GeForce RTX 4090',
                'vendor': 'NVIDIA',
                'gpu_type': 'discrete',
                'compute_framework': 'cuda',
                'memory': 24000000000,  # 24GB
                'utilization': random.randint(20, 80),
                'memory_used': random.randint(5000000000, 15000000000),
                'temperature': random.randint(45, 75),
                'power': random.randint(150, 350),
                'metrics_accurate': True
            }
        ],
        'active_jobs': random.randint(0, 2),
        'completed_jobs': len([j for j in mock_jobs if j['status'] == 'completed']),
        'wallet_address': mock_wallet_address,
        'balance': mock_balance,
        'status': 'running'
    }

@app.get("/api/jobs")
async def get_jobs():
    """Mock jobs endpoint"""
    return {'jobs': mock_jobs}

@app.get("/api/earnings")
async def get_earnings():
    """Mock earnings endpoint"""
    total_earnings = sum(j['reward'] for j in mock_jobs if j['status'] == 'completed')
    today_earnings = sum(
        j['reward'] for j in mock_jobs 
        if j['status'] == 'completed' and 
        (datetime.now() - datetime.fromisoformat(j['completed_at'])).days == 0
    )
    
    return {
        'total_earnings': total_earnings,
        'today_earnings': today_earnings,
        'completed_jobs': len([j for j in mock_jobs if j['status'] == 'completed']),
        'failed_jobs': len([j for j in mock_jobs if j['status'] == 'failed'])
    }

@app.post("/api/start")
async def start_agent():
    """Mock start endpoint"""
    return {'status': 'started'}

@app.post("/api/stop")
async def stop_agent():
    """Mock stop endpoint"""
    return {'status': 'stopped'}

@app.get("/api/marketplace/jobs")
async def get_marketplace_jobs():
    """Get available marketplace jobs - GPU only"""
    return {
        'jobs': [
            {
                'job_id': f'job_{i:04d}',
                'job_type': job_type,
                'docker_image': 'python:3.11-slim',
                'reward': round(random.uniform(0.0001, 0.005), 6),
                'gpu_memory_required': gpu_mem * 1e9,
                'requires_gpu': True,
                'estimated_duration': random.randint(30, 300),
                'timeout': random.randint(300, 600)
            }
            for i, (job_type, gpu_mem) in enumerate([
                ('inference', 8),
                ('training', 24),
                ('rendering', 16),
                ('text-generation', 12),
                ('ml-inference', 8),
                ('video-processing', 16),
                ('3d-rendering', 24),
                ('model-training', 40),
            ])
        ]
    }

@app.get("/api/marketplace/agents")
async def get_marketplace_agents():
    """Get available compute agents"""
    return {
        'agents': [
            {
                'id': f'agent_{i:04d}',
                'gpu_model': gpu_model,
                'gpu_vendor': vendor,
                'gpu_memory': memory * 1e9,
                'compute_framework': framework,
                'status': 'available',
                'jobs_completed': random.randint(50, 500),
                'uptime': f'{random.randint(95, 99)}%',
                'rate': round(random.uniform(0.0005, 0.002), 6),
                'gpu_count': 1
            }
            for i, (gpu_model, vendor, memory, framework) in enumerate([
                ('RTX 4090', 'NVIDIA', 24, 'CUDA'),
                ('RTX 3090', 'NVIDIA', 24, 'CUDA'),
                ('RTX 4080', 'NVIDIA', 16, 'CUDA'),
                ('A100', 'NVIDIA', 80, 'CUDA'),
                ('H100', 'NVIDIA', 80, 'CUDA'),
                ('Radeon RX 7900 XTX', 'AMD', 24, 'ROCm'),
                ('RTX 3080', 'NVIDIA', 12, 'CUDA'),
                ('V100', 'NVIDIA', 32, 'CUDA'),
            ])
        ]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            await asyncio.sleep(2)
            
            # Send mock status with varying GPU utilization
            status = {
                'gpus': [
                    {
                        'index': 0,
                        'name': 'NVIDIA GeForce RTX 4090',
                        'vendor': 'NVIDIA',
                        'gpu_type': 'discrete',
                        'compute_framework': 'cuda',
                        'memory': 24000000000,
                        'utilization': random.randint(20, 80),
                        'memory_used': random.randint(5000000000, 15000000000),
                        'temperature': random.randint(45, 75),
                        'power': random.randint(150, 350),
                        'metrics_accurate': True
                    }
                ],
                'active_jobs': random.randint(0, 2),
                'completed_jobs': len([j for j in mock_jobs if j['status'] == 'completed']),
                'wallet_address': mock_wallet_address,
                'balance': mock_balance,
                'status': 'running'
            }
            
            await websocket.send_json(status)
            
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  node3 Marketplace UI Test Server")
    print("="*60)
    print("\n✨ Starting dashboards with mock data...")
    print(f"\n🎮 Agent Dashboard:     http://localhost:8080")
    print(f"🏪 Marketplace Browser: http://localhost:8080/marketplace")
    print("\n📋 What's included:")
    print("   • Agent Dashboard - Monitor your GPU and earnings")
    print("   • Marketplace - Browse jobs and compute providers")
    print("   • Live updates via WebSocket")
    print("   • Light/Dark theme support")
    print("\nThis is a test server with mock data to preview the UI.")
    print("Press Ctrl+C to stop.\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")

