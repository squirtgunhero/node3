#!/bin/bash
echo "Testing node3-agent executable..."

# Test 1: File exists and is executable
if [ ! -f "dist/node3-agent" ]; then
    echo "❌ Executable not found!"
    exit 1
fi
echo "✓ Executable found"

# Test 2: Is executable
if [ ! -x "dist/node3-agent" ]; then
    echo "Making executable..."
    chmod +x dist/node3-agent
fi
echo "✓ Executable has execute permissions"

# Test 3: File type
file_type=$(file dist/node3-agent)
echo "✓ File type: $file_type"

# Test 4: Check size
size=$(du -h dist/node3-agent | cut -f1)
echo "✓ File size: $size"

echo ""
echo "All basic checks passed!"
echo "Run './dist/node3-agent' to test execution"
