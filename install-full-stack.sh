#!/bin/bash
# iTaK Full Stack Installer
# Automatically installs Docker and all iTaK services (Neo4j, SearXNG, Weaviate)

set -e

echo "🚀 iTaK Full Stack Installer"
echo "════════════════════════════════════════"
echo "This will install:"
echo "  ✓ Docker (if missing)"
echo "  ✓ iTaK Agent"
echo "  ✓ Neo4j (Knowledge Graph)"
echo "  ✓ Weaviate (Vector Database)"
echo "  ✓ SearXNG (Private Web Search)"
echo "════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check and install Docker
check_docker() {
    if command_exists docker; then
        echo -e "${GREEN}✅ Docker found${NC}"
        docker --version
    else
        echo -e "${YELLOW}❌ Docker not found${NC}"
        echo ""
        echo "Docker is required for full stack installation."
        read -p "Install Docker now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            echo "Running prerequisite installer..."
            ./install-prerequisites.sh
        else
            echo -e "${RED}❌ Docker is required for full stack. Exiting.${NC}"
            exit 1
        fi
    fi
    
    # Check docker-compose
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Compose found${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker Compose not found${NC}"
        echo "Installing Docker Compose plugin..."
        sudo apt-get update && sudo apt-get install -y docker-compose-plugin || \
        sudo dnf install -y docker-compose-plugin || \
        brew install docker-compose
    fi
}

# Create .env if it doesn't exist
setup_env() {
    if [ ! -f .env ]; then
        echo ""
        echo "📝 Creating .env configuration..."
        cp .env.example .env
        echo -e "${GREEN}✅ .env file created${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  Important: Add your API key to .env file${NC}"
        echo "At minimum, add ONE of:"
        echo "  - GEMINI_API_KEY=your_key_here"
        echo "  - OPENAI_API_KEY=your_key_here"
        echo "  - ANTHROPIC_API_KEY=your_key_here"
        echo ""
        read -p "Press Enter to continue (you can add keys later)..." 
    else
        echo -e "${GREEN}✅ .env file exists${NC}"
    fi
}

# Start services
start_services() {
    echo ""
    echo "🚀 Starting iTaK Full Stack..."
    echo "This may take a few minutes on first run (downloading images)..."
    echo ""
    
    # Use docker compose (new) or docker-compose (old)
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    # Pull images first to show progress
    echo "📦 Pulling Docker images..."
    $COMPOSE_CMD pull
    
    echo ""
    echo "🎬 Starting services..."
    $COMPOSE_CMD up -d
    
    echo ""
    echo -e "${GREEN}✅ Services started!${NC}"
}

# Wait for services to be ready
wait_for_services() {
    echo ""
    echo "⏳ Waiting for services to be ready..."
    echo ""
    
    # Wait for Neo4j
    echo -n "  Neo4j: "
    for i in {1..30}; do
        if curl -s http://localhost:47474 >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Ready${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for Weaviate
    echo -n "  Weaviate: "
    for i in {1..30}; do
        if curl -s http://localhost:48080/v1/.well-known/ready >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Ready${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for SearXNG
    echo -n "  SearXNG: "
    for i in {1..30}; do
        if curl -s http://localhost:48888 >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Ready${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
}

# Show connection info
show_info() {
    echo ""
    echo "════════════════════════════════════════"
    echo -e "${GREEN}🎉 iTaK Full Stack is ready!${NC}"
    echo "════════════════════════════════════════"
    echo ""
    echo "📊 Service URLs:"
    echo ""
    echo -e "  ${BLUE}Neo4j Browser:${NC}    http://localhost:47474"
    echo "    Username: neo4j"
    echo "    Password: changeme (change in .env)"
    echo ""
    echo -e "  ${BLUE}Weaviate:${NC}         http://localhost:48080"
    echo ""
    echo -e "  ${BLUE}SearXNG:${NC}          http://localhost:48888"
    echo ""
    echo "════════════════════════════════════════"
    echo ""
    echo "📝 Next Steps:"
    echo ""
    echo "  1. Configure API keys in .env file:"
    echo "     nano .env"
    echo ""
    echo "  2. Start iTaK agent:"
    echo "     python main.py --webui"
    echo ""
    echo "  3. Visit iTaK Web UI:"
    echo "     http://localhost:8000"
    echo ""
    echo "  4. Check service status:"
    echo "     docker compose ps"
    echo ""
    echo "  5. View logs:"
    echo "     docker compose logs -f"
    echo ""
    echo "  6. Stop services:"
    echo "     docker compose down"
    echo ""
    echo "════════════════════════════════════════"
}

# Main installation flow
main() {
    check_docker
    setup_env
    start_services
    wait_for_services
    show_info
}

main
