#!/usr/bin/env python3
"""
Node3 Agent Telemetry Server
Real-time monitoring of agent installations and status
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import sqlite3
import json
import asyncio
import uvicorn

app = FastAPI(title="Node3 Agent Telemetry")

# WebSocket connections for real-time updates
active_connections: List[WebSocket] = []

# Database setup
def init_db():
    conn = sqlite3.connect('telemetry.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS agents (
        agent_id TEXT PRIMARY KEY,
        mac_address TEXT,
        hostname TEXT,
        platform TEXT,
        platform_version TEXT,
        agent_version TEXT,
        gpu_vendor TEXT,
        gpu_model TEXT,
        gpu_memory INTEGER,
        gpu_count INTEGER,
        first_seen TEXT,
        last_seen TEXT,
        status TEXT,
        ip_address TEXT,
        country TEXT,
        city TEXT,
        total_jobs INTEGER DEFAULT 0,
        total_earnings REAL DEFAULT 0.0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT,
        event_type TEXT,
        timestamp TEXT,
        data TEXT,
        FOREIGN KEY(agent_id) REFERENCES agents(agent_id)
    )''')
    
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class AgentTelemetry(BaseModel):
    agent_id: str
    mac_address: str
    hostname: str
    platform: str
    platform_version: str
    agent_version: str
    gpu_vendor: str
    gpu_model: str
    gpu_memory: int
    gpu_count: int = 1
    ip_address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None

class AgentHeartbeat(BaseModel):
    agent_id: str
    status: str  # 'online', 'idle', 'working', 'offline'
    total_jobs: Optional[int] = None
    total_earnings: Optional[float] = None

class AgentEvent(BaseModel):
    agent_id: str
    event_type: str  # 'started', 'stopped', 'job_completed', 'error'
    data: Optional[Dict] = None

# API Endpoints
@app.post("/api/telemetry/register")
async def register_agent(telemetry: AgentTelemetry):
    """Register a new agent or update existing"""
    conn = sqlite3.connect('telemetry.db')
    c = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    
    # Check if agent exists
    c.execute("SELECT agent_id FROM agents WHERE agent_id = ?", (telemetry.agent_id,))
    existing = c.fetchone()
    
    if existing:
        # Update existing agent
        c.execute("""UPDATE agents SET
            mac_address = ?, hostname = ?, platform = ?, platform_version = ?,
            agent_version = ?, gpu_vendor = ?, gpu_model = ?, gpu_memory = ?,
            gpu_count = ?, last_seen = ?, status = ?, ip_address = ?,
            country = ?, city = ?
            WHERE agent_id = ?""",
            (telemetry.mac_address, telemetry.hostname, telemetry.platform,
             telemetry.platform_version, telemetry.agent_version, telemetry.gpu_vendor,
             telemetry.gpu_model, telemetry.gpu_memory, telemetry.gpu_count,
             now, 'online', telemetry.ip_address, telemetry.country, telemetry.city,
             telemetry.agent_id))
    else:
        # Insert new agent
        c.execute("""INSERT INTO agents (
            agent_id, mac_address, hostname, platform, platform_version,
            agent_version, gpu_vendor, gpu_model, gpu_memory, gpu_count,
            first_seen, last_seen, status, ip_address, country, city
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (telemetry.agent_id, telemetry.mac_address, telemetry.hostname,
             telemetry.platform, telemetry.platform_version, telemetry.agent_version,
             telemetry.gpu_vendor, telemetry.gpu_model, telemetry.gpu_memory,
             telemetry.gpu_count, now, now, 'online', telemetry.ip_address,
             telemetry.country, telemetry.city))
        
        # Log event
        c.execute("INSERT INTO events (agent_id, event_type, timestamp, data) VALUES (?, ?, ?, ?)",
                  (telemetry.agent_id, 'registered', now, json.dumps(telemetry.dict())))
    
    conn.commit()
    conn.close()
    
    # Broadcast update to all connected clients
    await broadcast_update()
    
    return {"status": "success", "agent_id": telemetry.agent_id}

@app.post("/api/telemetry/heartbeat")
async def agent_heartbeat(heartbeat: AgentHeartbeat):
    """Receive agent heartbeat"""
    conn = sqlite3.connect('telemetry.db')
    c = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    
    # Update agent status
    update_query = "UPDATE agents SET last_seen = ?, status = ?"
    params = [now, heartbeat.status]
    
    if heartbeat.total_jobs is not None:
        update_query += ", total_jobs = ?"
        params.append(heartbeat.total_jobs)
    
    if heartbeat.total_earnings is not None:
        update_query += ", total_earnings = ?"
        params.append(heartbeat.total_earnings)
    
    update_query += " WHERE agent_id = ?"
    params.append(heartbeat.agent_id)
    
    c.execute(update_query, params)
    conn.commit()
    conn.close()
    
    # Broadcast update
    await broadcast_update()
    
    return {"status": "success"}

@app.post("/api/telemetry/event")
async def log_event(event: AgentEvent):
    """Log agent event"""
    conn = sqlite3.connect('telemetry.db')
    c = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    c.execute("INSERT INTO events (agent_id, event_type, timestamp, data) VALUES (?, ?, ?, ?)",
              (event.agent_id, event.event_type, now, json.dumps(event.data or {})))
    
    conn.commit()
    conn.close()
    
    await broadcast_update()
    
    return {"status": "success"}

@app.get("/api/agents")
async def get_all_agents():
    """Get all registered agents"""
    conn = sqlite3.connect('telemetry.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Mark agents as offline if last seen > 2 minutes ago
    cutoff = (datetime.utcnow() - timedelta(minutes=2)).isoformat()
    c.execute("UPDATE agents SET status = 'offline' WHERE last_seen < ? AND status != 'offline'", (cutoff,))
    conn.commit()
    
    c.execute("SELECT * FROM agents ORDER BY last_seen DESC")
    agents = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return {"agents": agents}

@app.get("/api/stats")
async def get_stats():
    """Get overall statistics"""
    conn = sqlite3.connect('telemetry.db')
    c = conn.cursor()
    
    # Mark offline agents
    cutoff = (datetime.utcnow() - timedelta(minutes=2)).isoformat()
    c.execute("UPDATE agents SET status = 'offline' WHERE last_seen < ? AND status != 'offline'", (cutoff,))
    conn.commit()
    
    # Total agents
    c.execute("SELECT COUNT(*) FROM agents")
    total_agents = c.fetchone()[0]
    
    # Online agents
    c.execute("SELECT COUNT(*) FROM agents WHERE status = 'online' OR status = 'working'")
    online_agents = c.fetchone()[0]
    
    # Platform breakdown
    c.execute("SELECT platform, COUNT(*) FROM agents GROUP BY platform")
    platforms = dict(c.fetchall())
    
    # GPU vendors
    c.execute("SELECT gpu_vendor, COUNT(*) FROM agents GROUP BY gpu_vendor")
    gpu_vendors = dict(c.fetchall())
    
    # Total jobs and earnings
    c.execute("SELECT SUM(total_jobs), SUM(total_earnings) FROM agents")
    jobs, earnings = c.fetchone()
    
    # Recent events
    c.execute("""SELECT event_type, COUNT(*) FROM events 
                 WHERE timestamp > datetime('now', '-24 hours')
                 GROUP BY event_type""")
    recent_events = dict(c.fetchall())
    
    conn.close()
    
    return {
        "total_agents": total_agents,
        "online_agents": online_agents,
        "offline_agents": total_agents - online_agents,
        "platforms": platforms,
        "gpu_vendors": gpu_vendors,
        "total_jobs": jobs or 0,
        "total_earnings": earnings or 0.0,
        "recent_events": recent_events
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive and wait for messages
            data = await websocket.receive_text()
            # Echo back or handle commands
            await websocket.send_text(json.dumps({"status": "ok"}))
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_update():
    """Broadcast update to all connected WebSocket clients"""
    if active_connections:
        # Get current stats
        stats = await get_stats()
        agents = await get_all_agents()
        
        message = json.dumps({
            "type": "update",
            "stats": stats,
            "agents": agents
        })
        
        # Send to all connected clients
        for connection in active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

# Serve the dashboard HTML
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    with open('marketplace_monitor.html', 'r') as f:
        return f.read()

# Alternative dashboard (table view)
@app.get("/table", response_class=HTMLResponse)
async def serve_table_dashboard():
    with open('admin_dashboard.html', 'r') as f:
        return f.read()

if __name__ == "__main__":
    import os
    # Use Railway's PORT environment variable or default to 8888
    port = int(os.environ.get("PORT", 8888))
    
    print("🚀 Starting Node3 Telemetry Server")
    print(f"📊 Dashboard: http://0.0.0.0:{port}")
    print(f"🔌 WebSocket: ws://0.0.0.0:{port}/ws")
    uvicorn.run(app, host="0.0.0.0", port=port)

