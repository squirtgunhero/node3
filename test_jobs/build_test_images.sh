#!/bin/bash
# Build test Docker images for node3 agent
# This script builds all test job Docker images

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$SCRIPT_DIR"

echo "=========================================="
echo "Building node3 Test Job Docker Images"
echo "=========================================="
echo ""

# Build simple test image
echo "[1/3] Building simple test image..."
docker build -f Dockerfile.test-simple -t node3-test-simple:latest . || {
    echo "WARNING: Failed to build simple test image. Make sure Docker is running."
    exit 1
}
echo "✓ Simple test image built"
echo ""

# Build math test image
echo "[2/3] Building math computation test image..."
docker build -f Dockerfile.test-math -t node3-test-math:latest . || {
    echo "WARNING: Failed to build math test image."
    exit 1
}
echo "✓ Math test image built"
echo ""

# Build file processing test image
echo "[3/3] Building file processing test image..."
docker build -f Dockerfile.test-file-process -t node3-test-file-process:latest . || {
    echo "WARNING: Failed to build file processing test image."
    exit 1
}
echo "✓ File processing test image built"
echo ""

echo "=========================================="
echo "All test images built successfully!"
echo "=========================================="
echo ""
echo "Available images:"
docker images | grep "node3-test" || echo "No node3-test images found"


