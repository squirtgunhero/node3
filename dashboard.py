# dashboard.py

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from typing import Dict, List
from datetime import datetime
from loguru import logger
import os

app = FastAPI(title="node3 Agent Dashboard")

# Templates directory
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
templates = Jinja2Templates(directory=templates_dir)

class Dashboard:
    """Dashboard server for node3 agent"""
    
    def __init__(self, 
                 gpu_detector,
                 job_manager,
                 payment_module,
                 port: int = 8080):
        self.gpu_detector = gpu_detector
        self.job_manager = job_manager
        self.payment_module = payment_module
        self.port = port
        self.active_websockets: List[WebSocket] = []
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """Main dashboard page"""
            return templates.TemplateResponse("index.html", {
                "request": request
            })
            
        @app.get("/api/status")
        async def get_status():
            """Get current agent status"""
            gpus = self.gpu_detector.gpus
            
            # Update GPU detector with active job count for better metrics
            active_job_count = len(self.job_manager.active_jobs)
            if hasattr(self.gpu_detector, '_active_job_count'):
                self.gpu_detector._active_job_count = active_job_count
            
            gpu_data = []
            for gpu in gpus:
                util = self.gpu_detector.get_gpu_utilization(gpu.index)
                gpu_data.append({
                    'index': gpu.index,
                    'name': gpu.name,
                    'vendor': gpu.vendor,
                    'gpu_type': gpu.gpu_type.value if hasattr(gpu.gpu_type, 'value') else str(gpu.gpu_type),
                    'compute_framework': gpu.compute_framework.value if hasattr(gpu.compute_framework, 'value') else str(gpu.compute_framework),
                    'memory': gpu.total_memory,
                    'utilization': util.get('gpu_utilization', 0),
                    'memory_used': util.get('memory_used', 0),
                    'temperature': util.get('temperature', 0),
                    'power': util.get('power_usage', 0),
                    'metrics_accurate': util.get('metrics_accurate', False)  # True if real measurements
                })
            
            # Get wallet balance
            try:
                balance = await self.payment_module.get_balance()
            except Exception as e:
                logger.error(f"Error getting balance: {e}")
                balance = 0.0
                
            return {
                'gpus': gpu_data,
                'active_jobs': active_job_count,
                'completed_jobs': len(self.job_manager.job_history),
                'wallet_address': self.payment_module.get_wallet_address(),
                'balance': float(balance),  # Ensure it's a float, not a string
                'status': 'running' if self.job_manager.is_running else 'stopped'
            }
            
        @app.get("/api/jobs")
        async def get_jobs():
            """Get job history"""
            jobs = []
            
            for job in self.job_manager.job_history[-50:]:  # Last 50 jobs
                jobs.append({
                    'job_id': job.job_id,
                    'job_type': job.job_type,
                    'status': job.status.value,
                    'reward': job.reward,
                    'duration': (job.completed_at - job.started_at).total_seconds() if job.completed_at and job.started_at else None,
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None
                })
                
            return {'jobs': jobs}
            
        @app.get("/api/earnings")
        async def get_earnings():
            """Get earnings statistics"""
            total_earnings = sum(job.reward for job in self.job_manager.job_history if job.status.value == 'completed')
            
            today_earnings = sum(
                job.reward for job in self.job_manager.job_history 
                if job.status.value == 'completed' and 
                job.completed_at and 
                job.completed_at.date() == datetime.now().date()
            )
            
            return {
                'total_earnings': total_earnings,
                'today_earnings': today_earnings,
                'completed_jobs': len([j for j in self.job_manager.job_history if j.status.value == 'completed']),
                'failed_jobs': len([j for j in self.job_manager.job_history if j.status.value == 'failed'])
            }
            
        @app.post("/api/start")
        async def start_agent():
            """Start the agent"""
            if not self.job_manager.is_running:
                import asyncio
                asyncio.create_task(self.job_manager.start())
                return {'status': 'started'}
            return {'status': 'already_running'}
            
        @app.post("/api/stop")
        async def stop_agent():
            """Stop the agent"""
            self.job_manager.stop()
            return {'status': 'stopped'}
            
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates"""
            await websocket.accept()
            self.active_websockets.append(websocket)
            
            try:
                while True:
                    # Send status updates every 2 seconds
                    import asyncio
                    await asyncio.sleep(2)
                    
                    # Get status data
                    gpus = self.gpu_detector.gpus
                    gpu_data = []
                    for gpu in gpus:
                        util = self.gpu_detector.get_gpu_utilization(gpu.index)
                        gpu_data.append({
                            'index': gpu.index,
                            'name': gpu.name,
                            'vendor': gpu.vendor,
                            'gpu_type': gpu.gpu_type.value if hasattr(gpu.gpu_type, 'value') else str(gpu.gpu_type),
                            'compute_framework': gpu.compute_framework.value if hasattr(gpu.compute_framework, 'value') else str(gpu.compute_framework),
                            'memory': gpu.total_memory,
                            'utilization': util.get('gpu_utilization', 0),
                            'memory_used': util.get('memory_used', 0),
                            'temperature': util.get('temperature', 0),
                            'power': util.get('power_usage', 0)
                        })
                    
                    status = {
                        'gpus': gpu_data,
                        'active_jobs': len(self.job_manager.active_jobs),
                        'completed_jobs': len(self.job_manager.job_history),
                        'wallet_address': self.payment_module.get_wallet_address(),
                        'balance': await self.payment_module.get_balance(),
                        'status': 'running' if self.job_manager.is_running else 'stopped'
                    }
                    
                    await websocket.send_json(status)
                    
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                if websocket in self.active_websockets:
                    self.active_websockets.remove(websocket)
                
    async def start(self):
        """Start the dashboard server"""
        self.setup_routes()
        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

