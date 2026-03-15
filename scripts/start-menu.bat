@echo off
REM Neighborhood BBS - Local Launcher Menu
REM Choose between local-only or network mode

setlocal enabledelayedexpansion

cls
echo.
echo ========================================
echo Neighborhood BBS - Start Menu
echo ========================================
echo.
echo Choose how to run the server:
echo.
echo   1. Local Only (127.0.0.1:8080)
echo      ^> Access from this computer only
echo      ^> Most secure
echo.
echo   2. Network Access (0.0.0.0:8080)
echo      ^> Access from any device on WiFi
echo      ^> Share with neighbors
echo.
echo   3. Custom Port
echo      ^> Same as option 1, different port
echo.
echo   4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    call :RunLocal
) else if "%choice%"=="2" (
    call :RunNetwork
) else if "%choice%"=="3" (
    call :RunCustom
) else if "%choice%"=="4" (
    exit /b 0
) else (
    echo Invalid choice. Try again.
    timeout /t 2 >nul
    goto start
)

goto :eof

:RunLocal
echo.
echo Starting Neighborhood BBS - LOCAL ONLY mode...
echo Access at: http://localhost:8080
echo.
call .\scripts\run-local.ps1
goto :eof

:RunNetwork
echo.
echo Starting Neighborhood BBS - NETWORK ACCESS mode...
echo.
for /f "tokens=4" %%a in ('route print ^| find " 0.0.0.0"') do set gateway=%%a
for /f "tokens=2 delims=: " %%a in ('ipconfig ^| find "IPv4"') do set localip=%%a
echo Access locally:  http://localhost:8080
echo Access network:  http://!localip!:8080
echo.
call .\scripts\run-local.ps1 -Network
goto :eof

:RunCustom
echo.
set /p port="Enter custom port (default 8080): "
if "!port!"=="" set port=8080
echo Starting Neighborhood BBS on port !port!...
echo Access at: http://localhost:!port!
echo.
call .\scripts\run-local.ps1 -Port !port!
goto :eof
