@echo off
cd /d "%~dp0"
title StreamMix Studio Launcher

:: Unblock any files flagged by Windows SmartScreen/Mark of the Web
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -Path '%~dp0' -Recurse -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue" >nul 2>&1

:: Start StreamMix Studio
if exist "StreamMixStudio.exe" (
    start "" "StreamMixStudio.exe"
) else (
    echo [ERROR] StreamMixStudio.exe not found in this folder!
    pause
)
