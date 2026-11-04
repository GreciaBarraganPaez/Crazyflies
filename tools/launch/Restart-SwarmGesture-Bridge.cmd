@echo off
cd /d "%~dp0..\.."
echo Run this after landing and stopping the old bridge with Ctrl+C.
powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-SwarmGesture.ps1" -Role bridge
