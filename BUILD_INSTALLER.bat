@echo off
setlocal enabledelayedexpansion
title StreamMix Studio - 1-Click Windows Setup Installer Builder
color 0b

echo =====================================================================
echo       STREAMMIX STUDIO - 1-CLICK WINDOWS SETUP INSTALLER
echo   Builds a real Windows Setup.exe with Desktop Icon and Native Window
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Verifying Python and dependencies...
set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=py
    ) else (
        color 0c
        echo [ERROR] Python is not installed or not in system PATH!
        pause
        exit /b 1
    )
)

%PYTHON_CMD% -c "import PyInstaller, webview" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing required packaging packages (pyinstaller, pywebview)...
    %PYTHON_CMD% -m pip install pyinstaller pywebview
)

echo.
echo [2/3] Building Compiled Application Binary (Native WebView2)...
if not exist "dist\StreamMixStudio\StreamMixStudio.exe" (
    echo [*] Compiling binary for the first time (may take 1-2 minutes)...
    call BUILD_EXE.bat
) else (
    echo [*] Existing compiled binary found in dist\StreamMixStudio.
    echo [*] If you want a fresh recompilation, delete the dist folder first.
)

echo.
echo [3/3] Generating Windows Setup Installer (Setup.exe)...
%PYTHON_CMD% tools\create_installer.py

if %errorlevel% neq 0 (
    color 0c
    echo.
    echo [ERROR] Installer generation failed!
    pause
    exit /b 1
)

color 0a
echo.
echo =====================================================================
echo    ALL DONE! Your Setup.exe is ready in the dist\ folder.
echo =====================================================================
pause
