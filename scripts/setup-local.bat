@echo off
REM Neighborhood BBS - Quick Setup for Windows (cmd.exe)
REM Run this batch file to setup the project

setlocal enabledelayedexpansion

cls
echo.
echo ========================================
echo Neighborhood BBS - Local Setup
echo ========================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo   OK - Found: %PYTHON_VERSION%
echo.

REM Create virtual environment
echo Setting up virtual environment...
if exist venv\ (
    echo   OK - Virtual environment already exists
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo   OK - Virtual environment created
)
echo.

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo   OK - Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
pip install -q --upgrade pip
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo   OK - Dependencies installed
echo.

REM Install dev dependencies
echo Installing dev dependencies...
pip install -r requirements-dev.txt -q
echo   OK - Dev dependencies installed
echo.

REM Create directories
echo Creating directories...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist data\backups mkdir data\backups
echo   OK - Directories created
echo.

REM Create .env file
echo Configuring environment...
if not exist .env (
    (
        echo # Neighborhood BBS - Local Configuration
        echo FLASK_ENV=development
        echo FLASK_DEBUG=True
        echo SECRET_KEY=%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%
        echo DATABASE_PATH=data/neighborhood_bbs.db
        echo LOG_PATH=logs/
        echo PORT=8080
        echo HOST=127.0.0.1
        echo LOG_LEVEL=INFO
    ) > .env
    echo   OK - Created .env
) else (
    echo   OK - .env already exists
)
echo.

REM Initialize database
echo Initializing database...
if exist data\neighborhood_bbs.db (
    echo   OK - Database already exists
) else (
    python scripts\init-db-local.py
    if errorlevel 1 (
        echo WARNING: Database initialization had issues
    ) else (
        echo   OK - Database created
    )
)
echo.

REM Create admin user
echo Creating admin user...
python -c "import sqlite3; conn = sqlite3.connect('data/neighborhood_bbs.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM admin_users'); print(cursor.fetchone()[0])" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo   OK - Admin user exists
) else (
    echo   Running admin user setup...
    python scripts\create_admin_user.py
)
echo.

REM Success
echo ========================================
echo SUCCESS - Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Run the app:
echo      scripts\run-local.bat
echo.
echo   2. Open browser:
echo      http://localhost:8080
echo.
echo   3. Admin login:
echo      http://localhost:8080/admin/login
echo.
pause
