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

echo [1/3] Verifying Python Environment...
set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=py
    ) else (
        color 0c
        echo [ERROR] Python is not installed or not in system PATH!
        echo Please install Python 3.10+ from https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo [2/3] Verifying Core Dependencies...
%PYTHON_CMD% -c "import fastapi, uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Core dependencies missing. Installing requirements.txt automatically...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        color 0c
        echo [ERROR] Dependency installation failed! Check internet connection.
        pause
        exit /b 1
    )
)

echo [3/3] Launching Native Desktop Workstation Window...
%PYTHON_CMD% desktop_launcher.py

if %errorlevel% neq 0 (
    color 0c
    echo.
    echo [ERROR] StreamMix Studio stopped with an error. Check logs in data\logs\error.log
    pause
)
