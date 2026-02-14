@echo off
REM iTaK Prerequisites Installer for Windows
REM Automatically installs or guides installation of Docker Desktop, Python, and Git

echo ========================================
echo iTaK Prerequisites Installer (Windows)
echo ========================================
echo.

REM Check for Docker Desktop
docker --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Docker Desktop already installed
    docker --version
    goto check_python
)

echo [!] Docker Desktop not found
echo.
echo Docker Desktop is recommended for running iTaK.
echo.
choice /C YN /M "Would you like to download and install Docker Desktop?"
if errorlevel 2 goto check_python
if errorlevel 1 goto install_docker

:install_docker
echo.
echo Opening Docker Desktop download page...
start https://docs.docker.com/desktop/install/windows-install/
echo.
echo Please:
echo   1. Download Docker Desktop for Windows
echo   2. Run the installer
echo   3. Restart your computer if prompted
echo   4. Start Docker Desktop from the Start Menu
echo   5. Wait for Docker to start (whale icon in system tray)
echo   6. Re-run this script
echo.
pause
goto end

:check_python
echo.
REM Check for Python 3.11+
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto python_not_found

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% LSS 3 goto python_too_old
if %PYTHON_MAJOR% EQU 3 if %PYTHON_MINOR% LSS 11 goto python_too_old

echo [OK] Python %PYTHON_VERSION% found (3.11+ required)
python --version
goto check_git

:python_not_found
echo [!] Python not found
goto offer_python_install

:python_too_old
echo [!] Python %PYTHON_VERSION% found, but 3.11+ required
goto offer_python_install

:offer_python_install
echo.
echo Python 3.11+ is required for iTaK.
echo.
choice /C YN /M "Would you like to download Python 3.11?"
if errorlevel 2 goto check_git
if errorlevel 1 goto install_python

:install_python
echo.
echo Opening Python download page...
start https://www.python.org/downloads/
echo.
echo Please:
echo   1. Download Python 3.11 or later
echo   2. Run the installer
echo   3. IMPORTANT: Check "Add Python to PATH"
echo   4. Click "Install Now"
echo   5. Restart this script after installation
echo.
pause
goto end

:check_git
echo.
REM Check for Git
git --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Git already installed
    git --version
    goto prerequisites_complete
)

echo [!] Git not found
echo.
echo Git is required to clone the iTaK repository.
echo.
choice /C YN /M "Would you like to download Git for Windows?"
if errorlevel 2 goto prerequisites_complete
if errorlevel 1 goto install_git

:install_git
echo.
echo Opening Git for Windows download page...
start https://git-scm.com/download/win
echo.
echo Please:
echo   1. Download Git for Windows
echo   2. Run the installer
echo   3. Use default options
echo   4. Restart this script after installation
echo.
pause
goto end

:prerequisites_complete
echo.
echo ========================================
echo Prerequisites check complete!
echo ========================================
echo.

REM Check what's installed
docker --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set HAS_DOCKER=1
) else (
    set HAS_DOCKER=0
)

python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set HAS_PYTHON=1
) else (
    set HAS_PYTHON=0
)

git --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set HAS_GIT=1
) else (
    set HAS_GIT=0
)

echo Status:
if %HAS_DOCKER% EQU 1 (
    echo   [OK] Docker Desktop installed
) else (
    echo   [!] Docker Desktop missing
)
if %HAS_PYTHON% EQU 1 (
    echo   [OK] Python 3.11+ installed
) else (
    echo   [!] Python 3.11+ missing
)
if %HAS_GIT% EQU 1 (
    echo   [OK] Git installed
) else (
    echo   [!] Git missing
)
echo.

if %HAS_DOCKER% EQU 1 (
    echo Next steps:
    echo   1. Make sure Docker Desktop is running
    echo   2. Run: quick-install.bat
    echo   3. Visit: http://localhost:8000
) else if %HAS_PYTHON% EQU 1 (
    echo Next steps (Python installation):
    echo   1. Run: git clone https://github.com/David2024patton/iTaK.git
    echo   2. Run: cd iTaK
    echo   3. Run: pip install -r requirements.txt
    echo   4. Run: python main.py --webui
    echo   5. Visit: http://localhost:8000
) else (
    echo Please install missing prerequisites and run this script again.
    echo See PREREQUISITES.md for manual installation instructions.
)
echo.
echo For detailed instructions: PREREQUISITES.md
echo For quick start: QUICK_START.md

:end
echo.
pause
