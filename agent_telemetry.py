"""
Agent Telemetry Module
Sends anonymous telemetry data to the monitoring dashboard
"""

import requests
import uuid
import platform
import socket
import json
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AgentTelemetry:
    def __init__(self, telemetry_url: str = "http://localhost:8888"):
        self.telemetry_url = telemetry_url
        self.agent_id = self._get_or_create_agent_id()
        self.telemetry_enabled = True
        
    def _get_or_create_agent_id(self) -> str:
        """Get existing agent ID or create new one"""
        config_dir = Path.home() / '.node3-agent'
        config_dir.mkdir(exist_ok=True)
        agent_id_file = config_dir / 'agent_id'
        
        if agent_id_file.exists():
            return agent_id_file.read_text().strip()
        else:
            agent_id = str(uuid.uuid4())
            agent_id_file.write_text(agent_id)
            return agent_id
    
    def _get_mac_address(self) -> str:
        """Get MAC address of primary network interface"""
        try:
            import re
            if platform.system() == 'Windows':
                import subprocess
                result = subprocess.check_output(['getmac']).decode()
                mac = re.search(r'([\dA-Fa-f]{2}[:-]){5}([\dA-Fa-f]{2})', result)
                return mac.group(0) if mac else 'unknown'
            else:
                # Unix-like systems
                import subprocess
                if platform.system() == 'Darwin':  # macOS
                    result = subprocess.check_output(['ifconfig']).decode()
                else:  # Linux
                    result = subprocess.check_output(['ip', 'link']).decode()
                mac = re.search(r'([\dA-Fa-f]{2}:){5}[\dA-Fa-f]{2}', result)
                return mac.group(0) if mac else 'unknown'
        except Exception as e:
            logger.debug(f"Could not get MAC address: {e}")
            return 'unknown'
    
    def _get_location(self) -> tuple[Optional[str], Optional[str]]:
        """Get approximate location from IP (privacy-friendly)"""
        try:
            # Use ip-api.com (free, no API key required)
            response = requests.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('city'), data.get('country')
        except Exception as e:
            logger.debug(f"Could not get location: {e}")
        return None, None
    
    def register(self, gpu_info: dict, agent_version: str = "1.0.0"):
        """Register agent with telemetry server"""
        if not self.telemetry_enabled:
            return
        
        try:
            city, country = self._get_location()
            
            data = {
                'agent_id': self.agent_id,
                'mac_address': self._get_mac_address(),
                'hostname': socket.gethostname(),
                'platform': platform.system(),
                'platform_version': platform.release(),
                'agent_version': agent_version,
                'gpu_vendor': gpu_info.get('vendor', 'Unknown'),
                'gpu_model': gpu_info.get('name', 'Unknown'),
                'gpu_memory': gpu_info.get('total_memory', 0),
                'gpu_count': gpu_info.get('count', 1),
                'city': city,
                'country': country
            }
            
            response = requests.post(
                f"{self.telemetry_url}/api/telemetry/register",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("✓ Telemetry registered")
            else:
                logger.warning(f"Telemetry registration failed: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"Telemetry registration error: {e}")
    
    def send_heartbeat(self, status: str = 'online', total_jobs: int = 0, total_earnings: float = 0.0):
        """Send heartbeat to telemetry server"""
        if not self.telemetry_enabled:
            return
        
        try:
            data = {
                'agent_id': self.agent_id,
                'status': status,  # 'online', 'idle', 'working', 'offline'
                'total_jobs': total_jobs,
                'total_earnings': total_earnings
            }
            
            response = requests.post(
                f"{self.telemetry_url}/api/telemetry/heartbeat",
                json=data,
                timeout=5
            )
            
            if response.status_code != 200:
                logger.debug(f"Heartbeat failed: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"Heartbeat error: {e}")
    
    def log_event(self, event_type: str, data: dict = None):
        """Log an event to telemetry server"""
        if not self.telemetry_enabled:
            return
        
        try:
            payload = {
                'agent_id': self.agent_id,
                'event_type': event_type,  # 'started', 'stopped', 'job_completed', 'error'
                'data': data or {}
            }
            
            response = requests.post(
                f"{self.telemetry_url}/api/telemetry/event",
                json=payload,
                timeout=5
            )
            
            if response.status_code != 200:
                logger.debug(f"Event logging failed: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"Event logging error: {e}")


# Example usage
if __name__ == '__main__':
    # Example GPU info structure
    gpu_info = {
        'vendor': 'NVIDIA',
        'name': 'NVIDIA GeForce RTX 3080',
        'total_memory': 10737418240,  # 10 GB in bytes
        'count': 1
    }
    
    # Create telemetry instance
    telemetry = AgentTelemetry(telemetry_url="http://localhost:8888")
    
    # Register agent
    telemetry.register(gpu_info, agent_version="1.0.0")
    
    # Send heartbeat
    telemetry.send_heartbeat(status='online', total_jobs=5, total_earnings=0.025)
    
    # Log event
    telemetry.log_event('job_completed', {'job_id': 'job_001', 'duration': 120})

