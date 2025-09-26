@echo off
echo Starting NIC PDF Generator...
echo.

REM Kill any existing processes
taskkill /f /im "NIC PDF Generator.exe" 2>nul
taskkill /f /im "node.exe" 2>nul

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start the server in background
echo Starting server...
start /b node server.js

REM Wait for server to start
timeout /t 3 /nobreak >nul

REM Start the Electron app
echo Starting desktop app...
if exist "dist-electron\win-unpacked\NIC PDF Generator.exe" (
    start "" "dist-electron\win-unpacked\NIC PDF Generator.exe"
) else (
    echo Error: NIC PDF Generator.exe not found!
    echo Please run: npm run dist
    pause
)

echo.
echo App launched! You can close this window.
pause