@echo off
title StreamMix Studio - 1080p 60fps Remix Engine
color 0b
cls

echo =====================================================================
echo       STREAMMIX STUDIO - TWITCH + YOUTUBE REMIX ENGINE
echo          High-Speed Single-Pass GPU Desktop Workstation
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/2] Verifying Python Environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH! Please install Python 3.10+
    pause
    exit /b 1
)

echo [2/2] Launching Desktop App Window...
python desktop_launcher.py

pause
