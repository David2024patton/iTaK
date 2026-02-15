# WSL Auto-Installation Script for Windows
# Automatically installs and configures WSL 2 with Ubuntu

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  WSL 2 Auto-Installer for iTaK" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[!] This script requires administrator privileges" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor Yellow
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "  3. Navigate to iTaK folder" -ForegroundColor Yellow
    Write-Host "  4. Run: .\detect-and-setup-wsl.ps1" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# Check Windows version
$osInfo = Get-CimInstance -ClassName Win32_OperatingSystem
$buildNumber = [int]$osInfo.BuildNumber

Write-Host "[INFO] Detected: Windows $($osInfo.Caption)" -ForegroundColor Cyan
Write-Host "[INFO] Build: $buildNumber" -ForegroundColor Cyan
Write-Host ""

if ($buildNumber -lt 19041) {
    Write-Host "[!] WSL 2 requires Windows 10 version 2004 or higher" -ForegroundColor Red
    Write-Host "[!] Or Windows 11" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please update Windows first:" -ForegroundColor Yellow
    Write-Host "  Settings > Update & Security > Windows Update" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# Check if WSL is already installed
try {
    $wslInstalled = (wsl --list --quiet 2>$null)
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] WSL is already installed!" -ForegroundColor Green
        Write-Host ""
        wsl --list --verbose
        Write-Host ""
        Write-Host "You can now use iTaK in WSL:" -ForegroundColor Green
        Write-Host "  1. Type: wsl" -ForegroundColor Green
        Write-Host "  2. Navigate to iTaK folder" -ForegroundColor Green
        Write-Host "  3. Run: ./install.sh" -ForegroundColor Green
        Write-Host ""
        pause
        exit 0
    }
} catch {
    # WSL not installed, continue
}

Write-Host "[INFO] Installing WSL 2..." -ForegroundColor Yellow
Write-Host ""

# Install WSL using the simplified command (Windows 10 2004+)
try {
    Write-Host "Running: wsl --install" -ForegroundColor Cyan
    wsl --install -d Ubuntu-22.04
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "================================================================" -ForegroundColor Green
        Write-Host "  WSL 2 Installation Complete!" -ForegroundColor Green
        Write-Host "================================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "What was installed:" -ForegroundColor Cyan
        Write-Host "  - WSL 2 (Windows Subsystem for Linux)" -ForegroundColor White
        Write-Host "  - Ubuntu 22.04 LTS" -ForegroundColor White
        Write-Host ""
        Write-Host "IMPORTANT: You must restart your computer!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "After restart:" -ForegroundColor Cyan
        Write-Host "  1. Open Windows Terminal or PowerShell" -ForegroundColor White
        Write-Host "  2. Type: wsl" -ForegroundColor White
        Write-Host "  3. Set up Ubuntu username and password (first time only)" -ForegroundColor White
        Write-Host "  4. Navigate to iTaK: cd /mnt/c/Users/$env:USERNAME/..." -ForegroundColor White
        Write-Host "  5. Run: ./install.sh" -ForegroundColor White
        Write-Host ""
        
        $restart = Read-Host "Restart now? (Y/N)"
        if ($restart -eq 'Y' -or $restart -eq 'y') {
            Write-Host ""
            Write-Host "Restarting in 10 seconds..." -ForegroundColor Yellow
            Write-Host "Press Ctrl+C to cancel" -ForegroundColor Yellow
            Start-Sleep -Seconds 10
            Restart-Computer
        }
    } else {
        throw "wsl --install failed"
    }
} catch {
    Write-Host ""
    Write-Host "[!] Automatic installation failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual installation steps:" -ForegroundColor Yellow
    Write-Host "  1. Open PowerShell as Administrator" -ForegroundColor White
    Write-Host "  2. Run: wsl --install" -ForegroundColor White
    Write-Host "  3. Restart your computer" -ForegroundColor White
    Write-Host "  4. Open PowerShell and type: wsl" -ForegroundColor White
    Write-Host "  5. Run iTaK installer: ./install.sh" -ForegroundColor White
    Write-Host ""
    Write-Host "For help: https://docs.microsoft.com/windows/wsl/install" -ForegroundColor Cyan
    Write-Host ""
    pause
    exit 1
}
