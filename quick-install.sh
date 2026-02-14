#!/bin/bash
# iTaK Quick Install Script (Agent-Zero Style)
# One-command installation for quick testing and demos

set -e

echo "🚀 iTaK Quick Install"
echo "─────────────────────────────────────"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker found"

# Check if we have a pre-built image
if docker pull david2024patton/itak:latest 2>/dev/null; then
    echo "✅ Using pre-built image from Docker Hub"
    IMAGE="david2024patton/itak:latest"
else
    echo "ℹ️  Pre-built image not found, building locally..."
    
    # Build the standalone image
    if [ -f "Dockerfile.standalone" ]; then
        docker build -f Dockerfile.standalone -t itak:latest .
        IMAGE="itak:latest"
        echo "✅ Built local image"
    else
        echo "❌ Dockerfile.standalone not found"
        echo "   Please run this script from the iTaK directory"
        exit 1
    fi
fi

echo ""
echo "🎉 iTaK is ready to run!"
echo "─────────────────────────────────────"
echo ""
echo "Starting iTaK..."
echo ""

# Run the container
docker run -it --rm \
    -p 8000:8000 \
    -v itak-data:/app/data \
    --name itak \
    $IMAGE

echo ""
echo "─────────────────────────────────────"
echo "✅ iTaK stopped"
