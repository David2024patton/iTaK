#!/bin/bash
# iTaK Prerequisites Installer
# Automatically installs Docker, Python, and Git based on detected OS

set -e

echo "🔧 iTaK Prerequisites Installer"
echo "════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$ID
            VER=$VERSION_ID
        else
            OS="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        echo -e "${RED}❌ Unsupported OS: $OSTYPE${NC}"
        exit 1
    fi
    
    echo "Detected OS: $OS"
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Docker on Ubuntu/Debian
install_docker_debian() {
    echo "📦 Installing Docker on Ubuntu/Debian..."
    
    sudo apt-get update
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✅ Docker installed${NC}"
    echo -e "${YELLOW}⚠️  You may need to log out and back in for docker group to take effect${NC}"
}

# Install Docker on Fedora/RHEL
install_docker_fedora() {
    echo "📦 Installing Docker on Fedora/RHEL..."
    
    sudo dnf -y install dnf-plugins-core
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}✅ Docker installed and started${NC}"
}

# Install Docker on macOS
install_docker_macos() {
    echo "📦 Installing Docker on macOS..."
    
    if ! command_exists brew; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    brew install --cask docker
    
    echo -e "${GREEN}✅ Docker Desktop installed${NC}"
    echo -e "${YELLOW}⚠️  Please start Docker Desktop from Applications folder${NC}"
}

# Install Python 3.11+
install_python() {
    echo "📦 Installing Python 3.11+..."
    
    case $OS in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y software-properties-common
            sudo add-apt-repository -y ppa:deadsnakes/ppa
            sudo apt-get update
            sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
            ;;
        fedora|rhel|centos)
            sudo dnf install -y python3.11 python3.11-devel python3.11-pip
            ;;
        macos)
            brew install python@3.11
            ;;
        *)
            echo -e "${YELLOW}⚠️  Cannot auto-install Python on $OS${NC}"
            echo "Please install Python 3.11+ manually from https://www.python.org/downloads/"
            return 1
            ;;
    esac
    
    echo -e "${GREEN}✅ Python installed${NC}"
}

# Install Git
install_git() {
    echo "📦 Installing Git..."
    
    case $OS in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y git
            ;;
        fedora|rhel|centos)
            sudo dnf install -y git
            ;;
        macos)
            xcode-select --install 2>/dev/null || true
            brew install git 2>/dev/null || true
            ;;
        *)
            echo -e "${YELLOW}⚠️  Cannot auto-install Git on $OS${NC}"
            return 1
            ;;
    esac
    
    echo -e "${GREEN}✅ Git installed${NC}"
}

# Main installation flow
main() {
    detect_os
    
    # Check Docker
    if command_exists docker; then
        echo -e "${GREEN}✅ Docker already installed${NC}"
        docker --version
    else
        echo -e "${YELLOW}❌ Docker not found${NC}"
        read -p "Install Docker? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            case $OS in
                ubuntu|debian)
                    install_docker_debian
                    ;;
                fedora|rhel|centos)
                    install_docker_fedora
                    ;;
                macos)
                    install_docker_macos
                    ;;
                *)
                    echo -e "${RED}❌ Docker auto-install not supported on $OS${NC}"
                    echo "Please install manually: https://docs.docker.com/get-docker/"
                    ;;
            esac
        fi
    fi
    
    echo ""
    
    # Check Python
    if command_exists python3.11 || command_exists python3 && python3 --version | grep -q "3\.1[1-9]"; then
        echo -e "${GREEN}✅ Python 3.11+ already installed${NC}"
        python3 --version 2>/dev/null || python3.11 --version
    else
        echo -e "${YELLOW}❌ Python 3.11+ not found${NC}"
        read -p "Install Python 3.11? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_python
        fi
    fi
    
    echo ""
    
    # Check Git
    if command_exists git; then
        echo -e "${GREEN}✅ Git already installed${NC}"
        git --version
    else
        echo -e "${YELLOW}❌ Git not found${NC}"
        read -p "Install Git? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_git
        fi
    fi
    
    echo ""
    echo "════════════════════════════════════════"
    echo -e "${GREEN}🎉 Prerequisites check complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. If Docker was just installed, log out and back in (or run: newgrp docker)"
    echo "  2. Run: ./quick-install.sh"
    echo "  3. Visit: http://localhost:8000"
    echo ""
    echo "For manual installation, see: PREREQUISITES.md"
}

main
