#!/bin/bash
# iTaK Quick Install Script (Agent-Zero Style)
# One-command installation for quick testing and demos

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 iTaK Quick Install"
echo "─────────────────────────────────────"
echo ""

# Ask for installation type if Docker is available
if command -v docker &> /dev/null; then
    echo "📦 Installation Type:"
    echo ""
    echo "  1. Minimal (iTaK only, fastest)"
    echo "  2. Full Stack (iTaK + Neo4j + SearXNG + Weaviate)"
    echo ""
    read -p "Choose installation type (1/2, default=1): " -n 1 -r
    echo ""
    echo ""
    
    if [[ $REPLY == "2" ]]; then
        echo "🚀 Starting Full Stack Installation..."
        "$SCRIPT_DIR/install-full-stack.sh"
        exit 0
    fi
    
    echo "📦 Continuing with Minimal Installation..."
    echo ""
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found"
    echo ""
    echo "📚 Installation options:"
    echo "   1. Auto-install: $SCRIPT_DIR/install-prerequisites.sh"
    echo "   2. Manual install: See PREREQUISITES.md"
    echo "   3. Use Python instead (fallback below)"
    echo ""
    read -p "Try Python installation instead? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "To install Docker: $SCRIPT_DIR/install-prerequisites.sh"
        echo "Or see: PREREQUISITES.md"
        exit 1
    fi
    
    # Python fallback
    echo ""
    echo "ℹ️  Falling back to Python installation..."
    
    # Check for Python
    if ! command -v python3 &> /dev/null && ! command -v python3.11 &> /dev/null; then
        echo "❌ Python 3.11+ not found either"
        echo ""
        echo "Please install prerequisites first:"
        echo "   ./install-prerequisites.sh"
        echo ""
        echo "Or see manual instructions: PREREQUISITES.md"
        exit 1
    fi
    
    # Run Python install
    echo "✅ Python found"
    echo "📦 Installing iTaK via Python..."
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Create .env if not exists
    if [ ! -f .env ]; then
        cp .env.example .env
        echo ""
        echo "⚠️  Please configure your API keys in .env file"
        echo "   At minimum, add ONE of:"
        echo "     - GEMINI_API_KEY=your_key"
        echo "     - OPENAI_API_KEY=your_key"
        echo ""
        read -p "Press Enter when ready to continue..."
    fi
    
    # Run iTaK
    echo "🚀 Starting iTaK..."
    python3 main.py --webui
    exit 0
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
