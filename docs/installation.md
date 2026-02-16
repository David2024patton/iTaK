# iTaK Installation Guide

## At a Glance
- Audience: New users, operators, and developers setting up iTaK environments.
- Scope: Guide environment setup from prerequisites to first successful launch with validation checkpoints.
- Last reviewed: 2026-02-16.

## Quick Start
- Verify prerequisites and environment variables before running setup scripts.
- Execute installation steps in order from [root/INSTALL.md](root/INSTALL.md).
- Confirm service readiness with [root/QUICK_START.md](root/QUICK_START.md).

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Use commands as ordered steps; verify prerequisites before launching services.
- Re-validate service ports and env/config files after any setup change.


This guide covers installation on all supported platforms: **macOS**, **Linux**, **Windows**, and **WSL** (Windows Subsystem for Linux).

## Quick Start (Automated Setup)

The easiest way to install iTaK is using our automated setup script:

### macOS / Linux / WSL

```bash
# 1. Clone the repository
git clone https://github.com/David2024patton/iTaK.git
cd iTaK

# 2. Run the setup script
bash installers/setup.sh
```

Or directly with Python:
```bash
python3 installers/setup.py
```

### Windows

```cmd
REM 1. Clone the repository
git clone https://github.com/David2024patton/iTaK.git
cd iTaK

REM 2. Run the setup script
installers\setup.bat
```

Or directly with Python:
```cmd
python installers/setup.py
```

## What the Setup Script Does

The automated setup script will:

1. ✅ **Detect your operating system** (Mac, Linux, Windows, WSL)
2. ✅ **Check Python version** (requires 3.11+)
3. ✅ **Verify pip is available**
4. ✅ **Check for git and docker** (recommended but optional)
5. ✅ **Create virtual environment** (if not already in one)
6. ✅ **Install all Python dependencies** from requirements.txt
7. ✅ **Install Playwright browsers** for web automation
8. ✅ **Copy configuration files** (.env and config.json from examples)
9. ✅ **Create required directories** (data/, logs/)
10. ✅ **Provide next steps** and usage instructions

## Prerequisites

### Required

- **Python 3.11 or higher**
  - Check your version: `python --version` or `python3 --version`
  - Download from: https://www.python.org/downloads/

- **pip** (Python package installer)
  - Usually comes with Python
  - Check: `pip --version` or `pip3 --version`

### Recommended

- **Git** (for cloning the repository and version control)
  - macOS: `brew install git`
  - Ubuntu/Debian: `sudo apt install git`
  - Windows: https://git-scm.com/download/win

- **Docker** (for sandboxed code execution)
  - All platforms: https://docs.docker.com/get-docker/

### Optional

- **At least one LLM API key** (or use local Ollama)
  - OpenAI: https://platform.openai.com/api-keys
  - Anthropic: https://console.anthropic.com/
  - Google Gemini: https://makersuite.google.com/app/apikey
  - Or use **Ollama** locally (no API key needed): https://ollama.ai

## Platform-Specific Installation

### macOS

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python 3.11+**:
   ```bash
   brew install python@3.11
   ```

3. **Clone and setup iTaK**:
   ```bash
   git clone https://github.com/David2024patton/iTaK.git
   cd iTaK
   bash setup.sh
   ```

### Ubuntu / Debian Linux

1. **Update package list**:
   ```bash
   sudo apt update
   ```

2. **Install Python 3.11+**:
   ```bash
   sudo apt install python3.11 python3.11-venv python3-pip git
   ```

3. **Clone and setup iTaK**:
   ```bash
   git clone https://github.com/David2024patton/iTaK.git
   cd iTaK
   bash setup.sh
   ```

### Fedora / RHEL / CentOS

1. **Install Python 3.11+**:
   ```bash
   sudo dnf install python3.11 python3-pip git
   ```

2. **Clone and setup iTaK**:
   ```bash
   git clone https://github.com/David2024patton/iTaK.git
   cd iTaK
   bash setup.sh
   ```

### Arch Linux

1. **Install Python**:
   ```bash
   sudo pacman -S python python-pip git
   ```

2. **Clone and setup iTaK**:
   ```bash
   git clone https://github.com/David2024patton/iTaK.git
   cd iTaK
   bash setup.sh
   ```

### Windows

1. **Install Python 3.11+**:
   - Download from https://www.python.org/downloads/
   - **Important**: Check "Add Python to PATH" during installation

2. **Install Git** (optional but recommended):
   - Download from https://git-scm.com/download/win

3. **Clone and setup iTaK**:
   ```cmd
   git clone https://github.com/David2024patton/iTaK.git
   cd iTaK
   setup.bat
   ```

### WSL (Windows Subsystem for Linux)

WSL users can follow the **Ubuntu/Debian** or **Fedora** instructions above, depending on your WSL distribution.

To check your WSL distribution:
```bash
lsb_release -a
```

## Manual Installation

If you prefer to install manually or the automated setup fails:

### 1. Clone the Repository

```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
```

### 2. Create Virtual Environment

**macOS / Linux / WSL:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r install/requirements/requirements.txt
```

### 4. Install Playwright Browsers

```bash
playwright install chromium
```

### 5. Copy Configuration Files

**macOS / Linux / WSL:**
```bash
cp install/config/.env.example .env
cp install/config/config.json.example config.json
```

**Windows:**
```cmd
copy install\config\.env.example .env
copy install\config\config.json.example config.json
```

### 6. Create Data Directories

```bash
mkdir -p data logs
```

## Post-Installation Configuration

### 1. Configure API Keys

Edit `.env` and add at least one LLM API key:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Or Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...

# Or Google Gemini
GEMINI_API_KEY=AIza...

# Or use local Ollama (no key needed)
OLLAMA_BASE_URL=http://localhost:11434
```

### 2. Configure iTaK Settings

Edit `config.json` to customize:
- **Model preferences** (which LLMs to use)
- **Memory backends** (SQLite, Neo4j, Weaviate)
- **Adapter settings** (Discord, Telegram, Slack)
- **WebUI configuration**

See `docs/config.md` for detailed config options.

### 3. Run Diagnostic

Verify everything is set up correctly:

```bash
python -m app.main --doctor
```

This will check:
- Python version and packages
- Configuration files
- API keys
- Service connectivity (Neo4j, Weaviate, etc.)
- File structure
- Security modules

## Running iTaK

Once setup is complete, you can run iTaK in various modes:

### CLI Mode (Terminal Chat)
```bash
python -m app.main
```

### With WebUI Dashboard
```bash
python -m app.main --webui
```
Then open http://localhost:48920 in your browser.

### Discord Bot
```bash
python -m app.main --adapter discord --webui
```

### Telegram Bot
```bash
python -m app.main --adapter telegram --webui
```

### Slack Bot
```bash
python -m app.main --adapter slack --webui
```

### WebUI Only (No Chat Adapter)
```bash
python -m app.main --webui-only
```

## Docker Installation

For containerized deployment:

### Using Docker Compose

```bash
docker compose --project-directory . -f install/docker/docker-compose.yml up -d
```

### Using Dockerfile

```bash
docker build -t itak .
docker run -d \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/data:/app/data \
  -p 48920:48920 \
  itak
```

## Troubleshooting

### Python Version Issues

**Problem**: "Python 3.11+ required"

**Solution**:
- macOS: `brew install python@3.11`
- Ubuntu: `sudo apt install python3.11`
- Windows: Download from https://www.python.org/downloads/

### Virtual Environment Activation

**Problem**: Cannot activate virtual environment

**Solution**:
- Make sure you're in the iTaK directory
- On Windows, try: `venv\Scripts\activate.bat` or `venv\Scripts\Activate.ps1`
- On Mac/Linux, try: `source venv/bin/activate`

### Playwright Installation Fails

**Problem**: `playwright install chromium` fails

**Solution**:
```bash
# Install system dependencies (Linux only)
sudo apt install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
  libxfixes3 libxrandr2 libgbm1 libasound2

# Then retry
playwright install chromium
```

### Permission Denied on Scripts

**Problem**: `Permission denied` when running `setup.sh`

**Solution**:
```bash
chmod +x setup.sh
bash setup.sh
```

### Import Errors

**Problem**: `ModuleNotFoundError` when running iTaK

**Solution**:
1. Make sure virtual environment is activated
2. Reinstall dependencies: `pip install -r install/requirements/requirements.txt`
3. Check Python version: `python --version`

### API Key Issues

**Problem**: "No LLM API key found"

**Solution**:
1. Edit `.env` file and add your API key
2. Make sure the key starts with the correct prefix (sk-, sk-ant-, AIza, etc.)
3. Reload environment: Restart your terminal or re-source the .env file

## Getting Help

- **Documentation**: Check the `docs/` directory
- **Issues**: https://github.com/David2024patton/iTaK/issues
- **Discussions**: https://github.com/David2024patton/iTaK/discussions

## Next Steps

After installation:

1. Read [Getting Started Guide](getting-started.md)
2. Review [Configuration Guide](config.md)
3. Explore [Tools Documentation](tools.md)
4. Learn about [Memory System](memory.md)
5. Set up [Multi-Channel Adapters](adapters.md)

---

**Happy AI agent building! 🧠**
