#!/usr/bin/env python3
"""
Simple test script for CPU-only test jobs
This script simulates a compute job by processing data and writing results
"""

import os
import json
import time
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("node3 Test Job - CPU Only")
    print("=" * 60)
    
    # Simulate some computation
    print("\n[1/4] Starting job...")
    time.sleep(1)
    
    # Read input data if available
    input_dir = Path("/input")
    output_dir = Path("/output")
    
    print(f"[2/4] Checking input directory: {input_dir}")
    if input_dir.exists():
        input_files = list(input_dir.glob("*"))
        print(f"Found {len(input_files)} input file(s)")
    else:
        print("No input directory found (using default test data)")
    
    # Simulate computation
    print("[3/4] Processing data...")
    result = {
        "job_id": os.getenv("JOB_ID", "test-job"),
        "status": "completed",
        "computation_time": 5.0,
        "processed_items": 100,
        "timestamp": time.time()
    }
    
    # Perform a simple computation
    total = sum(range(1000000))  # Simple CPU work
    result["computation_result"] = total % 1000
    
    time.sleep(2)  # Simulate processing time
    
    # Write output
    print(f"[4/4] Writing results to {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "result.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print("\n" + "=" * 60)
    print("Job completed successfully!")
    print(f"Results written to: {output_file}")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

