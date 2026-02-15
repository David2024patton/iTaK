@echo off
REM iTaK Quick Install Script for Windows
REM One-command installation for quick testing and demos

echo ========================================
echo iTaK Quick Install (Windows)
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Docker Desktop not found
    echo.
    echo Installation options:
    echo   1. Auto-install: install-prerequisites.bat
    echo   2. Manual install: See PREREQUISITES.md
    echo   3. Use Python instead (fallback option)
    echo.
    choice /C YN /M "Try Python installation instead?"
    if errorlevel 2 goto docker_required
    if errorlevel 1 goto python_fallback
)

echo [OK] Docker found
echo.
goto docker_install

:docker_required
echo.
echo To install Docker Desktop: install-prerequisites.bat
echo Or see: PREREQUISITES.md
pause
exit /b 1

:python_fallback
echo.
echo [INFO] Falling back to Python installation...
echo.

REM Check for Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found either!
    echo.
    echo Please install prerequisites first:
    echo   install-prerequisites.bat
    echo.
    echo Or see manual instructions: PREREQUISITES.md
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.
echo Installing iTaK via Python...
pip install -r install/requirements/requirements.txt

REM Create .env if not exists
if not exist .env (
    copy install\config\.env.example .env
    echo.
    echo [!] Please configure your API keys in .env file
    echo     At minimum, add ONE of:
    echo       - GEMINI_API_KEY=your_key
    echo       - OPENAI_API_KEY=your_key
    echo.
    pause
)

echo Starting iTaK...
python -m app.main --webui
goto end

:docker_install

REM Try to pull pre-built image
echo Checking for pre-built image...
docker pull david2024patton/itak:latest 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Using pre-built image from Docker Hub
    set IMAGE=david2024patton/itak:latest
) else (
    echo [INFO] Pre-built image not found, building locally...
    
    REM Build the standalone image
    if exist install\docker\Dockerfile.standalone (
        docker build -f install\docker\Dockerfile.standalone -t itak:latest .
        if %ERRORLEVEL% NEQ 0 (
            echo ERROR: Build failed
            pause
            exit /b 1
        )
        set IMAGE=itak:latest
        echo [OK] Built local image
    ) else (
        echo ERROR: install\docker\Dockerfile.standalone not found
        echo Please run this script from the iTaK directory
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo iTaK is ready to run!
echo ========================================
echo.
echo Starting iTaK...
echo Web UI will be available at: http://localhost:8000
echo Press Ctrl+C to stop
echo.

REM Run the container
docker run -it --rm -p 8000:8000 -v itak-data:/app/data --name itak %IMAGE%

echo.
echo ========================================
echo iTaK stopped
echo ========================================
pause
