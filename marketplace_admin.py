#!/usr/bin/env python3
"""
node3 Marketplace Admin CLI
===========================

Command-line tool for managing the production marketplace.

Usage:
    python marketplace_admin.py --help
    python marketplace_admin.py create-job --type inference --reward 0.001
    python marketplace_admin.py stats
    python marketplace_admin.py list-agents
"""

import click
import requests
import json
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
MARKETPLACE_URL = os.getenv("MARKETPLACE_URL", "http://localhost:8000")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")


def make_request(method: str, endpoint: str, data: Optional[dict] = None):
    """Make authenticated request to marketplace"""
    headers = {
        "X-API-Key": ADMIN_API_KEY,
        "Content-Type": "application/json"
    }
    
    url = f"{MARKETPLACE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Error: {e}", err=True)
        if hasattr(e.response, 'text'):
            click.echo(f"   Response: {e.response.text}", err=True)
        return None


@click.group()
def cli():
    """node3 Marketplace Admin CLI"""
    if not ADMIN_API_KEY:
        click.echo("⚠️  Warning: ADMIN_API_KEY not set in environment", err=True)


@cli.command()
@click.option('--job-type', default='inference', help='Job type')
@click.option('--docker-image', default='python:3.11-slim', help='Docker image')
@click.option('--command', multiple=True, help='Command to run (can specify multiple)')
@click.option('--reward', type=float, default=0.001, help='Reward in SOL')
@click.option('--gpu-memory', type=int, default=0, help='Required GPU memory in bytes')
@click.option('--requires-gpu/--no-gpu', default=False, help='Requires GPU')
@click.option('--duration', type=int, default=60, help='Estimated duration in seconds')
@click.option('--timeout', type=int, default=300, help='Timeout in seconds')
def create_job(job_type, docker_image, command, reward, gpu_memory, requires_gpu, duration, timeout):
    """Create a new job in the marketplace"""
    
    # Default command if none provided
    if not command:
        command = ['python', '-c', 'print("Hello from node3!")']
    
    job_data = {
        "job_type": job_type,
        "docker_image": docker_image,
        "command": list(command),
        "environment": {},
        "gpu_memory_required": gpu_memory,
        "requires_gpu": requires_gpu,
        "estimated_duration": duration,
        "timeout": timeout,
        "reward": reward
    }
    
    click.echo(f"Creating job...")
    result = make_request("POST", "/api/admin/jobs/create", job_data)
    
    if result:
        click.echo(f"✅ Job created successfully!")
        click.echo(f"   Job ID: {result['job_id']}")
        click.echo(f"   Status: {result['status']}")


@cli.command()
def stats():
    """Get marketplace statistics"""
    click.echo("Fetching marketplace statistics...")
    
    result = make_request("GET", "/api/admin/stats")
    
    if result:
        click.echo("\n📊 Marketplace Statistics")
        click.echo("=" * 50)
        
        click.echo(f"\n👥 Agents:")
        click.echo(f"   Total: {result['agents']['total']}")
        
        click.echo(f"\n📋 Jobs:")
        click.echo(f"   Total: {result['jobs']['total']}")
        if result['jobs']['by_status']:
            for status, count in result['jobs']['by_status'].items():
                click.echo(f"   {status.capitalize()}: {count}")
        
        click.echo(f"\n💰 Payments:")
        click.echo(f"   Total Count: {result['payments']['total_count']}")
        click.echo(f"   Total Amount: {result['payments']['total_amount']:.6f} SOL")


@cli.command()
def wallet_info():
    """Get marketplace wallet information"""
    click.echo("Fetching marketplace wallet info...")
    
    result = make_request("GET", "/api/marketplace/info")
    
    if result:
        click.echo("\n💰 Marketplace Wallet")
        click.echo("=" * 50)
        click.echo(f"   Address: {result['wallet_address']}")
        click.echo(f"   Balance: {result['balance']:.6f} SOL")
        click.echo(f"   Escrow: {result['escrow_balance']:.6f} SOL")
        click.echo(f"   RPC: {result['rpc_url']}")
        click.echo(f"   Payments Processed: {result['payments_processed']}")
        click.echo(f"   Total Paid: {result['total_paid']:.6f} SOL")
        
        if result['balance'] < 1.0:
            click.echo("\n⚠️  Warning: Low balance! Fund wallet to continue paying agents.")


@cli.command()
def fund_wallet():
    """Request devnet SOL from faucet (devnet only)"""
    click.echo("Requesting 2 SOL from devnet faucet...")
    
    result = make_request("POST", "/api/marketplace/fund")
    
    if result:
        click.echo(f"✅ {result['message']}")
        click.echo(f"   New Balance: {result['new_balance']:.6f} SOL")


@cli.command()
def health():
    """Check marketplace health"""
    click.echo("Checking marketplace health...")
    
    result = make_request("GET", "/health")
    
    if result:
        status = result['status']
        
        if status == "healthy":
            click.echo(f"✅ Marketplace is {status}")
        else:
            click.echo(f"❌ Marketplace status: {status}")
        
        click.echo(f"   Database: {result.get('database', 'unknown')}")
        click.echo(f"   Payment System: {result.get('payment_system', 'unknown')}")
        click.echo(f"   Timestamp: {result.get('timestamp', 'unknown')}")


@cli.command()
def payment_history():
    """View payment history"""
    click.echo("Fetching payment history...")
    
    result = make_request("GET", "/api/payments/history")
    
    if result:
        payments = result.get('payments', [])
        
        if not payments:
            click.echo("No payments yet.")
            return
        
        click.echo(f"\n💸 Payment History ({len(payments)} payments)")
        click.echo("=" * 50)
        
        for payment in payments[-10:]:  # Show last 10
            click.echo(f"\nJob: {payment['job_id'][:8]}...")
            click.echo(f"   Agent: {payment['agent_wallet'][:8]}...")
            click.echo(f"   Amount: {payment['amount']} SOL")
            click.echo(f"   Status: {payment['status']}")
            click.echo(f"   Time: {payment['timestamp']}")
            click.echo(f"   TX: {payment['signature'][:16]}...")


@cli.command()
@click.option('--count', default=10, type=int, help='Number of test jobs to create')
@click.option('--reward', default=0.0001, type=float, help='Reward per job')
def create_test_jobs(count, reward):
    """Create multiple test jobs for testing"""
    click.echo(f"Creating {count} test jobs...")
    
    test_commands = [
        ['python', '-c', 'import time; time.sleep(5); print("Job 1 complete")'],
        ['python', '-c', 'print("Quick job"); print("Done")'],
        ['python', '-c', 'for i in range(10): print(f"Processing {i}")'],
    ]
    
    created = 0
    for i in range(count):
        job_data = {
            "job_type": "test",
            "docker_image": "python:3.11-slim",
            "command": test_commands[i % len(test_commands)],
            "environment": {},
            "gpu_memory_required": 0,
            "requires_gpu": False,
            "estimated_duration": 30,
            "timeout": 60,
            "reward": reward
        }
        
        result = make_request("POST", "/api/admin/jobs/create", job_data)
        
        if result:
            created += 1
            click.echo(f"  ✓ Created job {i+1}/{count} (ID: {result['job_id'][:8]}...)")
        else:
            click.echo(f"  ✗ Failed to create job {i+1}")
    
    click.echo(f"\n✅ Created {created}/{count} test jobs")


if __name__ == '__main__':
    cli()

