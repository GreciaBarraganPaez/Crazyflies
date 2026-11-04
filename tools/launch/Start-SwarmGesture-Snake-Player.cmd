@echo off
cd /d "%~dp0..\.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-SwarmGesture.ps1" -FormationMode snake-player -SimulationProfile preview
if errorlevel 1 pause
