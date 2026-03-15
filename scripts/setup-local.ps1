# Neighborhood BBS - Local Development Setup
# This script automates the setup process for Windows

param(
    [switch]$SkipPython = $false,
    [switch]$SkipDeps = $false,
    [switch]$Fresh = $false
)

$ErrorActionPreference = "Stop"

Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Neighborhood BBS - Local Setup          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "1️⃣  Checking Python..." -ForegroundColor Yellow
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($pythonPath) {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found in PATH" -ForegroundColor Red
    Write-Host "  Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  ⚠️  Make sure to check 'Add Python to PATH'" -ForegroundColor Yellow
    exit 1
}

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
Write-Host "  Working directory: $projectRoot" -ForegroundColor Gray

# Create virtual environment
Write-Host ""
Write-Host "2️⃣  Setting up virtual environment..." -ForegroundColor Yellow

if ((Test-Path "venv") -and $Fresh) {
    Write-Host "  Removing existing virtual environment..." -ForegroundColor Gray
    Remove-Item -Recurse -Force venv
}

if (-not (Test-Path "venv")) {
    Write-Host "  Creating venv..." -ForegroundColor Gray
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "  Activating venv..." -ForegroundColor Gray
$activateScript = "venv\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Host "✗ Activation script not found" -ForegroundColor Red
    exit 1
}

& $activateScript
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "3️⃣  Installing dependencies..." -ForegroundColor Yellow

if ($SkipDeps) {
    Write-Host "  Skipped (--SkipDeps)" -ForegroundColor Gray
} else {
    Write-Host "  Installing from requirements.txt..." -ForegroundColor Gray
    pip install -q --upgrade pip
    pip install -r requirements.txt -q
    Write-Host "✓ Dependencies installed" -ForegroundColor Green

    Write-Host "  Installing dev dependencies..." -ForegroundColor Gray
    pip install -r requirements-dev.txt -q
    Write-Host "✓ Dev dependencies installed" -ForegroundColor Green
}

# Create directories
Write-Host ""
Write-Host "4️⃣  Creating directories..." -ForegroundColor Yellow

$dirs = @("data", "logs", "data/backups")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory $dir -Force | Out-Null
        Write-Host "  ✓ Created $dir" -ForegroundColor Gray
    }
}

# Create .env file if it doesn't exist
Write-Host ""
Write-Host "5️⃣  Configuring environment..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "  Creating .env file..." -ForegroundColor Gray
    
    $secret = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString())) -Replace "[^a-zA-Z0-9]", ""
    
    @"
# Neighborhood BBS - Local Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=$secret
DATABASE_PATH=data/neighborhood_bbs.db
LOG_PATH=logs/
PORT=8080
HOST=127.0.0.1
LOG_LEVEL=INFO
"@ | Out-File -Encoding UTF8 .env
    
    Write-Host "✓ Created .env with default settings" -ForegroundColor Green
} else {
    Write-Host "✓ .env already exists" -ForegroundColor Green
}

# Initialize database
Write-Host ""
Write-Host "6️⃣  Initializing database..." -ForegroundColor Yellow

if ((Test-Path "data/neighborhood_bbs.db") -and $Fresh) {
    Write-Host "  Backing up existing database..." -ForegroundColor Gray
    $backup = "data/backups/neighborhood_bbs.db.$(Get-Date -Format 'yyyy-MM-dd-HHmmss')"
    Copy-Item data/neighborhood_bbs.db $backup
    Remove-Item data/neighborhood_bbs.db
    Write-Host "  ✓ Backed up to $backup" -ForegroundColor Gray
}

if (-not (Test-Path "data/neighborhood_bbs.db")) {
    Write-Host "  Creating database..." -ForegroundColor Gray
    python scripts/init-db-local.py | Out-Null
    Write-Host "✓ Database created" -ForegroundColor Green
} else {
    Write-Host "✓ Database already exists" -ForegroundColor Green
}

# Create admin user
Write-Host ""
Write-Host "7️⃣  Admin account setup..." -ForegroundColor Yellow

$adminExists = python -c "
import sqlite3
try:
    conn = sqlite3.connect('data/neighborhood_bbs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM admin_users WHERE username = \`admin\`')
    print(cursor.fetchone()[0] > 0)
except:
    print(False)
" 2>$null

if ($adminExists -eq "False" -or $adminExists -eq "") {
    Write-Host "  No admin user found. Creating..." -ForegroundColor Gray
    Write-Host ""
    python scripts/create_admin_user.py
    Write-Host ""
} else {
    Write-Host "✓ Admin user already exists" -ForegroundColor Green
}

# Final summary
Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✓ Setup Complete!                      ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Run the app:" -ForegroundColor Gray
Write-Host "      .\scripts\run-local.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "   2. Open browser:" -ForegroundColor Gray
Write-Host "      http://localhost:8080" -ForegroundColor Yellow
Write-Host ""
Write-Host "   3. Login:" -ForegroundColor Gray
Write-Host "      Username: admin" -ForegroundColor Yellow
Write-Host "      Password: (as you set above)" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   • Local setup: LOCAL_SETUP.md" -ForegroundColor Gray
Write-Host "   • Admin panel: docs/ADMIN_PANEL.md" -ForegroundColor Gray
Write-Host "   • Troubleshooting: docs/" -ForegroundColor Gray
Write-Host ""
