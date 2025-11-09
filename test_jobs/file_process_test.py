#!/usr/bin/env python3
"""
File processing test - reads input files and processes them
"""

import json
import time
import sys
from pathlib import Path

def process_file(file_path):
    """Process a single file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Simple processing: count lines, words, chars
        lines = content.split('\n')
        words = content.split()
        
        return {
            "filename": file_path.name,
            "lines": len(lines),
            "words": len(words),
            "characters": len(content),
            "processed": True
        }
    except Exception as e:
        return {
            "filename": file_path.name,
            "error": str(e),
            "processed": False
        }

def main():
    print("=" * 60)
    print("node3 File Processing Test")
    print("=" * 60)
    
    input_dir = Path("/input")
    output_dir = Path("/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "files_processed": [],
        "total_files": 0,
        "status": "completed"
    }
    
    if input_dir.exists():
        input_files = list(input_dir.glob("*"))
        input_files = [f for f in input_files if f.is_file()]
        
        print(f"\nFound {len(input_files)} file(s) to process")
        results["total_files"] = len(input_files)
        
        for file_path in input_files:
            print(f"Processing: {file_path.name}")
            result = process_file(file_path)
            results["files_processed"].append(result)
    else:
        print("\nNo input directory found - creating test file")
        # Create a test file
        test_file = input_dir / "test.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("This is a test file for node3 agent.\nIt contains multiple lines.\nProcessing test.")
        
        result = process_file(test_file)
        results["files_processed"].append(result)
        results["total_files"] = 1
    
    # Write results
    output_file = output_dir / "processing_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nProcessed {results['total_files']} file(s)")
    print(f"Results written to: {output_file}")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


