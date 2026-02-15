# iTaK Installation - ONE Command

## 🚀 Quick Install (All Platforms)

**ONE command works everywhere** — Linux, macOS, Windows (WSL), or WSL directly:

```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
python install.py
```

That's it! The installer will:
1. ✅ Auto-detect your operating system
2. ✅ Install prerequisites if needed (Docker, Git)
3. ✅ Ask: Minimal or Full Stack?
4. ✅ Configure everything automatically
5. ✅ Start iTaK

Then visit **http://localhost:8000** to access iTaK!

---

## 📋 Installation Options

### Interactive (Recommended)
```bash
python install.py
```
The installer will ask you questions and guide you through the process.

### Full Stack (All Databases)
```bash
python install.py --full-stack
```
Installs iTaK + Neo4j + Weaviate + SearXNG (production-ready setup).

### Minimal (iTaK Only)
```bash
python install.py --minimal
```
Installs just iTaK without databases (fastest, good for testing).

### Show Help
```bash
python install.py --help
```

---

## 🖥️ Platform Support

The Python installer works on:
- ✅ **Linux** (Ubuntu, Debian, Fedora, RHEL, CentOS, Arch)
- ✅ **macOS** (Intel and Apple Silicon)
- ✅ **WSL** (Windows Subsystem for Linux)
- ✅ **Windows** (via WSL - installer guides you through WSL setup)

---

## 📦 What Gets Installed

### Minimal Install
- ✅ iTaK AI agent
- ✅ Web UI (http://localhost:8000)
- ✅ SQLite database (local storage)
- ✅ Python dependencies
- ⏱️ Time: **2 minutes**

### Full Stack Install
- ✅ Everything in Minimal, plus:
- ✅ Neo4j (knowledge graph database)
- ✅ Weaviate (vector database for embeddings)
- ✅ SearXNG (private web search engine)
- ⏱️ Time: **5 minutes**

---

## 🔧 Prerequisites

The installer checks and installs:
- 🐍 **Python 3.11+** (required - you need this to run the installer)
- 🐳 **Docker** (for full stack)
- 📦 **Git** (for cloning the repository)

**Don't have Python 3.11+?**
- Ubuntu/Debian: `sudo apt install python3.11`
- Fedora: `sudo dnf install python3.11`
- macOS: `brew install python@3.11`
- Windows: Download from [python.org](https://www.python.org/downloads/)

---

## 🎯 Step-by-Step Walkthrough

### 1. Clone the Repository
```bash
git clone https://github.com/David2024patton/iTaK.git
cd iTaK
```

### 2. Run the Installer
```bash
python install.py
```

or on some systems:
```bash
python3 install.py
```

### 3. Follow the Prompts

The installer will:
- Detect your OS
- Check Python version
- Ask: Full Stack or Minimal?
- Install prerequisites if needed
- Install Python dependencies
- Configure .env file
- Start services

### 4. Configure API Keys

Edit `.env` and add at least ONE API key:
```bash
# Choose one or more:
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### 5. Access iTaK

Visit http://localhost:8000 in your browser!

---

## 🐛 Troubleshooting

### Python version too old
```
Error: Python 3.11+ required, but you have 3.9
```
**Solution:** Upgrade Python to 3.11 or later.

### Docker not found (Full Stack)
```
Error: Docker not found! Cannot start full stack.
```
**Solution:** 
- The installer tries to install Docker automatically on Linux
- On macOS, install Docker Desktop manually
- On Windows, use WSL and install Docker in WSL

### Permission denied
```
Error: Permission denied
```
**Solution:** On Linux, you may need to add your user to the docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### WSL on Windows
```
Windows detected. iTaK works best in WSL.
```
**Solution:** 
1. Open PowerShell as Administrator
2. Run: `wsl --install`
3. Restart your computer
4. Open Ubuntu from Start Menu
5. Clone iTaK and run `python3 install.py`

---

## 📚 More Information

- **Quick Start Guide:** [QUICK_START.md](QUICK_START.md)
- **Full Documentation:** [README.md](README.md)
- **Prerequisites Guide:** [PREREQUISITES.md](PREREQUISITES.md)
- **Database Guide:** [DATABASES.md](DATABASES.md)
- **Testing Guide:** [TESTING.md](TESTING.md)

---

## 🆚 Old Installation Scripts (Deprecated)

**You don't need these anymore!** Use `python install.py` instead.

The following scripts are kept for backwards compatibility but are deprecated:
- ~~install.sh~~ → Use `python install.py`
- ~~install.bat~~ → Use `python install.py`
- ~~quick-install.sh~~ → Use `python install.py --minimal`
- ~~quick-install.bat~~ → Use `python install.py --minimal`
- ~~install-full-stack.sh~~ → Use `python install.py --full-stack`
- ~~install-prerequisites.sh~~ → Use `python install.py` (auto-installs)
- ~~install-prerequisites.bat~~ → Use `python install.py` (auto-installs)

**Why?** ONE Python script is simpler, works on all platforms, and easier to maintain.

---

## ❓ Questions?

- GitHub Issues: https://github.com/David2024patton/iTaK/issues
- Documentation: https://github.com/David2024patton/iTaK
- Quick Start: [QUICK_START.md](QUICK_START.md)

---

**Happy installing! 🎉**

```bash
python install.py
```
