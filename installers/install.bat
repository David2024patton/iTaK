@echo off
REM iTaK Installation for Windows
REM Detects WSL and offers automatic installation

echo.
echo ========================================
echo iTaK Installation for Windows
echo ========================================
echo.

REM Check if WSL is installed
wsl --list --quiet >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] WSL detected!
    echo.
    echo iTaK is designed for WSL/Linux environments.
    echo.
    echo Opening WSL and running installer...
    echo.
    wsl bash -c "cd '%cd%' && ./install.sh"
    goto :end
)

echo [!] WSL not found
echo.
echo iTaK runs best in WSL (Windows Subsystem for Linux).
echo.
set /p INSTALL_WSL="Would you like to install WSL now? (Y/N): "

if /i "%INSTALL_WSL%"=="Y" (
    echo.
    echo [INFO] Installing WSL...
    echo This requires administrator privileges.
    echo.
    
    REM Run PowerShell script to install WSL
    powershell -ExecutionPolicy Bypass -File "%~dp0detect-and-setup-wsl.ps1"
    
    if %errorlevel% equ 0 (
        echo.
        echo ========================================
        echo [OK] WSL installation complete!
        echo ========================================
        echo.
        echo Next steps:
        echo   1. Restart your computer (required for WSL)
        echo   2. Open Windows Terminal or PowerShell
        echo   3. Type: wsl
        echo   4. Navigate to iTaK folder
        echo   5. Run: ./install.sh
        echo.
    ) else (
        echo.
        echo [!] WSL installation failed
        echo.
        echo Manual installation:
        echo   1. Open PowerShell as Administrator
        echo   2. Run: wsl --install
        echo   3. Restart your computer
        echo   4. Run this script again
        echo.
    )
) else (
    echo.
    echo [INFO] Continuing without WSL...
    echo.
    echo iTaK requires WSL or Linux/macOS to run.
    echo.
    echo Installation options:
    echo   1. Install WSL (recommended): Run this script and choose Y
    echo   2. Manual WSL install: PowerShell as Admin: wsl --install
    echo   3. Use Python directly: install-prerequisites.bat
    echo.
    echo For help: https://github.com/David2024patton/iTaK
)

:end
pause
