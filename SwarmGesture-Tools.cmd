@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\launch\Start-SwarmGesture.ps1" -Role menu
if errorlevel 1 pause
