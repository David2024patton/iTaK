# iTaK Prerequisites Installation Guide

## At a Glance
- Audience: New users, operators, and developers setting up iTaK environments.
- Scope: Guide environment setup from prerequisites to first successful launch with validation checkpoints.
- Last reviewed: 2026-02-16.

## Quick Start
- Verify prerequisites and environment variables before running setup scripts.
- Execute installation steps in order from [INSTALL.md](INSTALL.md).
- Confirm service readiness with [QUICK_START.md](QUICK_START.md).

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Use commands as ordered steps; verify prerequisites before launching services.
- Re-validate service ports and env/config files after any setup change.


Complete guide for installing all prerequisites needed to run iTaK.

## 📋 System Requirements

| Requirement | Minimum | Recommended | Notes |
|-------------|---------|-------------|-------|
| **RAM** | 4GB | 8GB+ | More for Neo4j/Weaviate |
| **Disk Space** | 5GB | 20GB+ | Includes Docker images |
| **CPU** | 2 cores | 4+ cores | Better for parallel tasks |
| **OS** | Linux, macOS, Windows | Linux preferred | Docker required |

## 🚀 Quick Install (Automatic)

We provide automatic installers that detect your OS and install everything needed:

### Linux / macOS
```bash
./installers/install-prerequisites.sh
```

### Windows
```cmd
installers/install-prerequisites.bat
```

These scripts will install:
- ✅ Docker (or skip if you prefer Python)
- ✅ Python 3.11+ (if not present)
- ✅ Git (if not present)

---

## 🐳 Docker Installation (Recommended)

Docker is the **easiest way** to run iTaK. Choose your OS below:

### Ubuntu / Debian

```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to docker group (no sudo needed)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Fedora / RHEL / CentOS

```bash
# Install Docker
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
```

### macOS

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Or download manually:
# https://docs.docker.com/desktop/install/mac-install/

# Start Docker Desktop from Applications folder

# Verify
docker --version
```

### Windows

1. **Download Docker Desktop:**
   - Visit: https://docs.docker.com/desktop/install/windows-install/
   - Download Docker Desktop for Windows
   - Or use our script: `installers/install-prerequisites.bat`

2. **Install:**
   - Run the installer
   - Follow the installation wizard
   - Restart when prompted

3. **Enable WSL 2 (if prompted):**
   ```powershell
   wsl --install
   ```

4. **Start Docker Desktop:**
   - Launch from Start Menu
   - Wait for Docker to start (whale icon in system tray)

5. **Verify:**
   ```cmd
   docker --version
   docker compose version
   ```

---

## 🐍 Python Installation (Alternative to Docker)

If you prefer Python over Docker, install Python 3.11+:

### Ubuntu / Debian

```bash
# Add deadsnakes PPA for latest Python
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update

# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Verify
python3.11 --version
```

### Fedora / RHEL

```bash
# Install Python 3.11
sudo dnf install -y python3.11 python3.11-devel python3.11-pip

# Verify
python3.11 --version
```

### macOS

```bash
# Using Homebrew
brew install python@3.11

# Verify
python3.11 --version
```

### Windows

1. **Download Python:**
   - Visit: https://www.python.org/downloads/
   - Download Python 3.11 or later
   - Or use our script: `installers/install-prerequisites.bat`

2. **Install:**
   - Run the installer
   - ✅ **Important:** Check "Add Python to PATH"
   - Click "Install Now"

3. **Verify:**
   ```cmd
   python --version
   pip --version
   ```

---

## 📦 Git Installation

### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install -y git
git --version
```

### Fedora / RHEL

```bash
sudo dnf install -y git
git --version
```

### macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Or via Homebrew
brew install git

git --version
```

### Windows

1. **Download:**
   - Visit: https://git-scm.com/download/win
   - Download Git for Windows
   - Or use our script: `installers/install-prerequisites.bat`

2. **Install:**
   - Run installer
   - Use default options
   - Select "Git from the command line and also from 3rd-party software"

3. **Verify:**
   ```cmd
   git --version
   ```

---

## ✅ Verification

After installation, verify everything works:

### Check Docker
```bash
docker --version
docker compose version
docker ps  # Should show running containers (if any)
```

### Check Python
```bash
python3 --version  # Should be 3.11 or higher
python3 -m pip --version
```

### Check Git
```bash
git --version  # Should be 2.0 or higher
```

### Check System Resources
```bash
# Linux/macOS
free -h  # Check available RAM
df -h    # Check disk space

# Windows
systeminfo | findstr Memory
```

---

## 🔧 Troubleshooting

### "Docker daemon not running"

**Linux:**
```bash
sudo systemctl start docker
sudo systemctl enable docker  # Start on boot
```

**macOS/Windows:**
- Start Docker Desktop from Applications/Start Menu
- Wait for whale icon to appear

### "Permission denied" when running Docker

```bash
# Add yourself to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker

# Verify
docker ps
```

### "Python not found" or wrong version

```bash
# Check all Python versions
which -a python python3 python3.11

# Create alias if needed
alias python=python3.11

# Or use specific version
python3.11 --version
```

### "pip install fails" or permission errors

```bash
# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

pip install -r install/requirements/requirements.txt
```

### "Out of disk space"

```bash
# Clean Docker images/containers
docker system prune -a

# Check disk usage
docker system df
df -h
```

### "Not enough RAM"

- Close unnecessary applications
- Increase Docker Desktop memory limit (Settings → Resources → Memory)
- For full install, ensure 8GB+ RAM available

---

## 🎯 What's Next?

Once prerequisites are installed:

### Option 1: Quick Start (2 minutes)
```bash
./installers/quick-install.sh  # Linux/macOS
installers/quick-install.bat   # Windows
```

### Option 2: Full Install (10 minutes)
```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
cp install/config/.env.example .env
# Edit .env with your API keys
docker compose --project-directory . -f install/docker/docker-compose.yml up -d
```

### Option 3: Python Install
```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
pip install -r install/requirements/requirements.txt
cp install/config/.env.example .env
# Edit .env with your API keys
python -m app.main --webui
```

---

## 📚 Additional Resources

- **Docker Documentation:** https://docs.docker.com/get-started/
- **Python Documentation:** https://docs.python.org/3/
- **Git Documentation:** https://git-scm.com/doc
- **iTaK Quick Start:** [QUICK_START.md](QUICK_START.md)
- **iTaK Full Guide:** [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)

---

## 💡 Tips

1. **Docker Desktop** is easiest for beginners (all platforms)
2. **Python install** gives you more control but requires more setup
3. **Full install** (`docker compose`) includes all services for production
4. **Quick install** (installers/quick-install.sh) is perfect for testing

Choose the path that matches your experience level and needs!

---

## ❓ Need Help?

- **GitHub Issues:** https://github.com/David2024patton/iTaK/issues
- **Documentation:** Full guides in `/docs`
- **Quick Start:** [QUICK_START.md](QUICK_START.md) for fastest path

Happy installing! 🚀
