#!/usr/bin/env python3
"""
Marketplace Integration Tests
==============================
Tests the marketplace UI and API integration.
"""

import requests
import sys
import time
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:8080"

def print_test(name, passed, details=""):
    """Print test result"""
    if passed:
        print(f"{Fore.GREEN}✓{Style.RESET_ALL} {name}")
        if details:
            print(f"  {Fore.CYAN}{details}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗{Style.RESET_ALL} {name}")
        if details:
            print(f"  {Fore.RED}{details}{Style.RESET_ALL}")
    return passed


def test_marketplace_page():
    """Test marketplace HTML page loads"""
    try:
        response = requests.get(f"{BASE_URL}/marketplace", timeout=5)
        passed = response.status_code == 200 and "node³ Marketplace" in response.text
        return print_test(
            "Marketplace page loads",
            passed,
            f"Status: {response.status_code}"
        )
    except Exception as e:
        return print_test("Marketplace page loads", False, str(e))


def test_jobs_api():
    """Test jobs API endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/marketplace/jobs", timeout=5)
        data = response.json()
        
        # Check response structure
        has_jobs = 'jobs' in data and len(data['jobs']) > 0
        
        # Check all jobs are GPU-only
        all_gpu = all(job.get('requires_gpu', False) for job in data['jobs'])
        
        # Check job structure
        first_job = data['jobs'][0] if data['jobs'] else {}
        required_fields = ['job_id', 'job_type', 'reward', 'gpu_memory_required', 'requires_gpu']
        has_fields = all(field in first_job for field in required_fields)
        
        passed = has_jobs and all_gpu and has_fields
        details = f"Jobs: {len(data['jobs'])}, All GPU: {all_gpu}, Has fields: {has_fields}"
        
        return print_test("Jobs API returns GPU-only jobs", passed, details)
    except Exception as e:
        return print_test("Jobs API returns GPU-only jobs", False, str(e))


def test_agents_api():
    """Test agents API endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/marketplace/agents", timeout=5)
        data = response.json()
        
        # Check response structure
        has_agents = 'agents' in data and len(data['agents']) > 0
        
        # Check agent structure
        first_agent = data['agents'][0] if data['agents'] else {}
        required_fields = ['id', 'gpu_model', 'gpu_vendor', 'gpu_memory', 'compute_framework', 'status']
        has_fields = all(field in first_agent for field in required_fields)
        
        # Check all have GPU
        all_have_gpu = all(
            agent.get('gpu_memory', 0) > 0 and agent.get('gpu_model')
            for agent in data['agents']
        )
        
        passed = has_agents and has_fields and all_have_gpu
        details = f"Agents: {len(data['agents'])}, Has fields: {has_fields}, All have GPU: {all_have_gpu}"
        
        return print_test("Agents API returns GPU providers", passed, details)
    except Exception as e:
        return print_test("Agents API returns GPU providers", False, str(e))


def test_dashboard_page():
    """Test main dashboard page loads"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        passed = response.status_code == 200 and "node³" in response.text
        return print_test(
            "Dashboard page loads",
            passed,
            f"Status: {response.status_code}"
        )
    except Exception as e:
        return print_test("Dashboard page loads", False, str(e))


def test_status_api():
    """Test status API endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=5)
        data = response.json()
        
        required_fields = ['gpus', 'active_jobs', 'completed_jobs', 'wallet_address', 'balance', 'status']
        has_fields = all(field in data for field in required_fields)
        
        passed = has_fields and response.status_code == 200
        details = f"Has all fields: {has_fields}"
        
        return print_test("Status API returns valid data", passed, details)
    except Exception as e:
        return print_test("Status API returns valid data", False, str(e))


def test_job_filtering():
    """Test that job filtering works correctly"""
    try:
        response = requests.get(f"{BASE_URL}/api/marketplace/jobs", timeout=5)
        data = response.json()
        
        # Check for different job types
        job_types = {job['job_type'] for job in data['jobs']}
        has_variety = len(job_types) > 1
        
        # Check GPU memory requirements vary
        gpu_memories = {job['gpu_memory_required'] for job in data['jobs']}
        has_memory_variety = len(gpu_memories) > 1
        
        passed = has_variety and has_memory_variety
        details = f"Job types: {len(job_types)}, Memory configs: {len(gpu_memories)}"
        
        return print_test("Job variety for filtering", passed, details)
    except Exception as e:
        return print_test("Job variety for filtering", False, str(e))


def test_ui_theme_support():
    """Test that UI has theme support"""
    try:
        response = requests.get(f"{BASE_URL}/marketplace", timeout=5)
        html = response.text
        
        # Check for theme-related CSS variables
        has_theme_vars = 'data-theme' in html or '--bg-primary' in html
        has_toggle = 'theme-toggle' in html or 'toggleTheme' in html
        
        passed = has_theme_vars and has_toggle
        details = "Theme CSS and toggle found" if passed else "Missing theme support"
        
        return print_test("UI has light/dark theme support", passed, details)
    except Exception as e:
        return print_test("UI has light/dark theme support", False, str(e))


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  node³ Marketplace Integration Tests")
    print("="*60 + "\n")
    
    print(f"Testing server at: {BASE_URL}\n")
    
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/health", timeout=1)
            print(f"{Fore.GREEN}Server is ready!{Style.RESET_ALL}\n")
            break
        except:
            if i == 9:
                print(f"{Fore.RED}Server not responding. Is test_dashboard_ui.py running?{Style.RESET_ALL}")
                print(f"Run: python3 test_dashboard_ui.py\n")
                sys.exit(1)
            time.sleep(0.5)
    
    # Run tests
    results = []
    
    print(f"{Fore.YELLOW}Testing Pages:{Style.RESET_ALL}")
    results.append(test_dashboard_page())
    results.append(test_marketplace_page())
    print()
    
    print(f"{Fore.YELLOW}Testing APIs:{Style.RESET_ALL}")
    results.append(test_status_api())
    results.append(test_jobs_api())
    results.append(test_agents_api())
    print()
    
    print(f"{Fore.YELLOW}Testing Features:{Style.RESET_ALL}")
    results.append(test_job_filtering())
    results.append(test_ui_theme_support())
    print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed ({percentage:.1f}%)")
    
    if passed == total:
        print(f"{Fore.GREEN}✓ All tests passed!{Style.RESET_ALL}")
        print("\n🎮 View the dashboard at: http://localhost:8080")
        print("🏪 View the marketplace at: http://localhost:8080/marketplace\n")
        sys.exit(0)
    else:
        print(f"{Fore.YELLOW}⚠ Some tests failed{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()

