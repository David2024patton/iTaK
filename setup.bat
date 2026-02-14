@echo off
REM iTaK Setup Script - Windows wrapper
REM Automatically detects Python and runs setup.py

setlocal enabledelayedexpansion

echo.
echo 🧠 iTaK Setup - Finding Python...
echo.

REM Try to find Python 3.11+
set PYTHON_CMD=

REM Try different Python commands
for %%p in (python3.12 python3.11 python3 python py) do (
    where %%p >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=2" %%v in ('%%p --version 2^>^&1') do (
            set VERSION=%%v
            for /f "tokens=1,2 delims=." %%a in ("!VERSION!") do (
                set MAJOR=%%a
                set MINOR=%%b
                REM Check if Python version is >= 3.11 (supports future major versions)
                if !MAJOR! gtr 3 (
                    set PYTHON_CMD=%%p
                    echo ✓ Found %%p (!VERSION!)
                    goto :found_python
                )
                if !MAJOR! equ 3 if !MINOR! geq 11 (
                    set PYTHON_CMD=%%p
                    echo ✓ Found %%p (!VERSION!)
                    goto :found_python
                )
            )
        )
    )
)

:found_python
if "%PYTHON_CMD%"=="" (
    echo ✗ Error: Python 3.11+ not found
    echo.
    echo Please install Python 3.11 or later from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Run setup.py
echo.
echo Running setup script with %PYTHON_CMD%...
echo.
%PYTHON_CMD% setup.py %*

if errorlevel 1 (
    echo.
    echo Setup failed!
    pause
    exit /b 1
)

echo.
pause
