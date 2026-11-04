@echo off
cd /d "%~dp0..\.."
echo.
echo Clean start will STOP ALL running WSL distributions and WSL-backed applications.
echo This can stop Docker Desktop containers and other Linux programs.
echo.
choice /C YN /M "Restart WSL and start SwarmGesture"
if errorlevel 2 exit /b 0
wsl.exe --shutdown
if errorlevel 1 (
    echo Could not shut down WSL.
    pause
    exit /b 1
)
timeout /t 3 /nobreak >nul
call "%~dp0..\..\Start-SwarmGesture.cmd"
