@echo off
cd /d "%~dp0..\.."
powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-SwarmGesture.ps1" -Role bridge -FormationMode snake -SimulationProfile preview
