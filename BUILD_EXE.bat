@echo off
setlocal enabledelayedexpansion
title StreamMix Studio - 1-Click Executable Builder
color 0b

echo =====================================================================
echo       STREAMMIX STUDIO - 1-CLICK STANDALONE EXE PACKAGER
echo   Creates a distributable, standalone desktop workstation folder
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Python is not installed or not in system PATH!
    echo Please install Python 3.10+ from python.org and try again.
    pause
    exit /b 1
)

echo [2/4] Verifying PyInstaller dependency...
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] PyInstaller not detected. Installing PyInstaller via pip...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        color 0c
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

echo [3/4] Building Standalone StreamMix Studio Executable...
echo [*] Bundling backend engine, frontend UI, and hardware binaries...
echo.

pyinstaller --noconfirm --onedir --windowed ^
    --name "StreamMixStudio" ^
    --add-data "backend;backend" ^
    --add-data "frontend;frontend" ^
    --add-data "bin;bin" ^
    --collect-all "uvicorn" ^
    --collect-all "fastapi" ^
    --collect-all "yt_dlp" ^
    --collect-all "webview" ^
    --collect-all "clr_loader" ^
    --collect-all "pythonnet" ^
    --hidden-import "webview" ^
    --hidden-import "clr_loader" ^
    --hidden-import "pythonnet" ^
    --hidden-import "backend" ^
    --hidden-import "backend.server" ^
    --hidden-import "backend.config" ^
    --hidden-import "backend.downloader" ^
    --hidden-import "backend.task_manager" ^
    --hidden-import "backend.turbo_renderer" ^
    --hidden-import "backend.subtitle_generator" ^
    --hidden-import "backend.groq_metadata" ^
    --hidden-import "backend.api_pool" ^
    desktop_launcher.py

if %errorlevel% neq 0 (
    color 0c
    echo.
    echo [ERROR] PyInstaller compilation failed! Check output above.
    pause
    exit /b 1
)

echo.
echo [4/4] Finalizing distribution package...
if not exist "dist\StreamMixStudio\data" mkdir "dist\StreamMixStudio\data"
if not exist "dist\StreamMixStudio\data\outputs" mkdir "dist\StreamMixStudio\data\outputs"
if not exist "dist\StreamMixStudio\data\downloads" mkdir "dist\StreamMixStudio\data\downloads"
if not exist "dist\StreamMixStudio\data\avatars" mkdir "dist\StreamMixStudio\data\avatars"
if not exist "dist\StreamMixStudio\data\bgm" mkdir "dist\StreamMixStudio\data\bgm"
if not exist "dist\StreamMixStudio\data\temp" mkdir "dist\StreamMixStudio\data\temp"
if not exist "dist\StreamMixStudio\data\logs" mkdir "dist\StreamMixStudio\data\logs"

if exist "data\avatars\default_avatar.png" (
    copy "data\avatars\default_avatar.png" "dist\StreamMixStudio\data\avatars\default_avatar.png" >nul 2>&1
)

color 0a
echo.
echo =====================================================================
echo    SUCCESS! StreamMix Studio has been built successfully!
echo =====================================================================
echo.
echo Distribution Path: %~dp0dist\StreamMixStudio\
echo Main Executable:   %~dp0dist\StreamMixStudio\StreamMixStudio.exe
echo.
echo How to share with others:
echo   1. Simply ZIP the entire "dist\StreamMixStudio" folder.
echo   2. Send the ZIP to any Windows user.
echo   3. They just extract and double-click "StreamMixStudio.exe"!
echo.
echo =====================================================================
pause
