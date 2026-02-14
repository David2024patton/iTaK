#!/bin/bash
# iTaK Setup Script - Unix/Linux/Mac/WSL wrapper
# Automatically detects Python and runs setup.py

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "🧠 iTaK Setup - Finding Python..."
echo ""

# Try to find Python 3.11+
PYTHON_CMD=""

# Try different Python commands
for cmd in python3.12 python3.11 python3 python; do
    if command -v "$cmd" &> /dev/null; then
        VERSION=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        MAJOR=$(echo $VERSION | cut -d. -f1)
        MINOR=$(echo $VERSION | cut -d. -f2)
        
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
            PYTHON_CMD="$cmd"
            echo -e "${GREEN}✓${NC} Found $cmd ($($cmd --version))"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}✗ Error: Python 3.11+ not found${NC}"
    echo ""
    echo "Please install Python 3.11 or later:"
    echo "  • macOS:   brew install python@3.11"
    echo "  • Ubuntu:  sudo apt install python3.11"
    echo "  • Fedora:  sudo dnf install python3.11"
    echo "  • Other:   https://www.python.org/downloads/"
    echo ""
    exit 1
fi

# Run setup.py
echo ""
echo "Running setup script with $PYTHON_CMD..."
echo ""
exec "$PYTHON_CMD" setup.py "$@"
