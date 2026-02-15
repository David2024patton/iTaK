# iTaK Installers

This directory contains various installation scripts for iTaK. These are alternative installation methods for users who prefer shell/batch scripts over the universal Python installer.

## 📋 Files Overview

### Universal Python Installer (Recommended)
**Location:** `/install.py` (in repository root)

The recommended way to install iTaK on all platforms. This is a standalone Python script that works on Linux, macOS, Windows, and WSL.

```bash
cd /path/to/iTaK
python install.py
```

### Shell Scripts (Linux/macOS/WSL)

- **`install.sh`** - Universal installer router that detects your OS
- **`setup.sh`** - Finds Python and runs setup.py
- **`setup.py`** - Interactive setup with virtual environment support
- **`quick-install.sh`** - One-command installation for quick testing
- **`install-full-stack.sh`** - Installs full stack with Docker (Neo4j, Weaviate, SearXNG)
- **`install-prerequisites.sh`** - Auto-installs prerequisites (Docker, Python, Git)

### Batch Scripts (Windows)

- **`install.bat`** - Windows installer with WSL detection
- **`setup.bat`** - Windows setup script
- **`quick-install.bat`** - Windows quick install
- **`install-prerequisites.bat`** - Auto-installs prerequisites on Windows

### PowerShell Scripts

- **`detect-and-setup-wsl.ps1`** - Auto-detects and installs WSL on Windows

## 🚀 Usage

### Quick Install
```bash
# Linux/macOS/WSL
./installers/quick-install.sh

# Windows
installers\quick-install.bat
```

### Full Stack Install
```bash
# Linux/macOS/WSL
./installers/install-full-stack.sh
```

### Interactive Setup
```bash
# Linux/macOS/WSL
python installers/setup.py

# Windows
python installers\setup.py
```

### Prerequisites Only
```bash
# Linux/macOS/WSL
./installers/install-prerequisites.sh

# Windows
installers\install-prerequisites.bat
```

## 📚 Documentation

For complete installation instructions, see:
- **[QUICK_START.md](../QUICK_START.md)** - Quick start guide
- **[INSTALL.md](../INSTALL.md)** - Installation overview
- **[INSTALLATION_GUIDE.md](../INSTALLATION_GUIDE.md)** - Detailed installation guide
- **[PREREQUISITES.md](../PREREQUISITES.md)** - Prerequisites installation guide

## 🔄 Migration from Old Structure

**Before:** All installer scripts were in the repository root  
**After:** All installer scripts are in the `installers/` directory

**What stayed in root:**
- `install.py` - Universal Python installer (recommended)
- `README.md` - Repository readme

**What moved to installers/:**
- All `.sh` scripts (install, setup, quick-install, etc.)
- All `.bat` scripts (install, setup, quick-install, etc.)
- All `.ps1` scripts (detect-and-setup-wsl)
- `setup.py` (interactive Python setup)

## ⚠️ Notes

- The **universal Python installer** (`install.py` in root) is the recommended installation method
- These alternative installers are provided for users who prefer shell/batch scripts
- All installers accomplish the same goal - getting iTaK up and running
- Choose the installation method that best fits your workflow
