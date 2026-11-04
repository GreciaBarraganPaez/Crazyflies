@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-SwarmGesture.ps1" -SimulationProfile preview
if errorlevel 1 pause
