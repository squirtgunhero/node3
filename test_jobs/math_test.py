#!/usr/bin/env python3
"""
Math computation test - CPU-intensive operations
"""

import json
import time
import sys
from pathlib import Path

def compute_pi_leibniz(iterations=1000000):
    """Approximate pi using Leibniz formula"""
    pi = 0.0
    for i in range(iterations):
        pi += (-1) ** i / (2 * i + 1)
    return pi * 4

def main():
    print("=" * 60)
    print("node3 Math Computation Test")
    print("=" * 60)
    
    print("\nComputing pi using Leibniz formula...")
    start_time = time.time()
    
    pi_approx = compute_pi_leibniz(iterations=5000000)
    
    elapsed = time.time() - start_time
    
    result = {
        "computation": "pi_approximation",
        "method": "leibniz_formula",
        "iterations": 5000000,
        "result": pi_approx,
        "elapsed_time": elapsed,
        "status": "completed"
    }
    
    print(f"Approximated pi: {pi_approx:.10f}")
    print(f"Computation time: {elapsed:.2f} seconds")
    
    # Write results
    output_dir = Path("/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "math_result.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("\nResults written to /output/math_result.json")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

