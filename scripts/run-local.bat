@echo off
REM Neighborhood BBS - Start Development Server
REM Quick launcher for running the BBS locally

setlocal enabledelayedexpansion

cls
echo.
echo ========================================
echo Neighborhood BBS - Development Server
echo ========================================
echo.

REM Check if venv exists
if not exist venv\Scripts\activate.bat (
    echo ERROR: Virtual environment not found!
    echo Please run setup first: scripts\setup-local.bat
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

REM Check if database exists
if not exist data\neighborhood_bbs.db (
    echo WARNING: Database not found. Initializing...
    python scripts\init-db-local.py
    if errorlevel 1 (
        echo ERROR: Failed to initialize database
        pause
        exit /b 1
    )
)

REM Set environment variables
set FLASK_APP=src\main.py
set FLASK_ENV=development
set FLASK_DEBUG=True

echo.
echo Starting server...
echo.
echo ================================================
echo Server running!
echo.
echo Access here: http://localhost:8080
echo Admin panel: http://localhost:8080/admin/login
echo API docs:    http://localhost:8080/api/docs
echo.
echo Press CTRL+C to stop the server
echo ================================================
echo.

REM Run Flask app
python src\main.py

pause
