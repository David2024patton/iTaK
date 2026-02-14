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
    echo ERROR: Docker not found!
    echo Please install Docker Desktop first:
    echo https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

echo [OK] Docker found
echo.

REM Try to pull pre-built image
echo Checking for pre-built image...
docker pull david2024patton/itak:latest 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Using pre-built image from Docker Hub
    set IMAGE=david2024patton/itak:latest
) else (
    echo [INFO] Pre-built image not found, building locally...
    
    REM Build the standalone image
    if exist Dockerfile.standalone (
        docker build -f Dockerfile.standalone -t itak:latest .
        if %ERRORLEVEL% NEQ 0 (
            echo ERROR: Build failed
            pause
            exit /b 1
        )
        set IMAGE=itak:latest
        echo [OK] Built local image
    ) else (
        echo ERROR: Dockerfile.standalone not found
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
