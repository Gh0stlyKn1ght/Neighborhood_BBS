# Neighborhood BBS - Local Development Launcher
# Activates venv and runs the Flask development server

param(
    [int]$Port = 8080,
    [string]$BindHost = "127.0.0.1",
    [switch]$Network = $false,  # Allow external connections
    [switch]$NoDebug = $false   # Disable debug mode
)

$ErrorActionPreference = "Stop"

# Colors
$success = "Green"
$warning = "Yellow" 
$info = "Cyan"
$error = "Red"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor $info
Write-Host "║  Neighborhood BBS - Development Server        ║" -ForegroundColor $info
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor $info
Write-Host ""

# Change to project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "📁 Project root: $projectRoot" -ForegroundColor Gray
Write-Host ""

# Check if venv exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor $error
    Write-Host "   Run setup first: .\scripts\setup-local.ps1" -ForegroundColor $warning
    exit 1
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor $info
& "venv\Scripts\Activate.ps1"

# Check if database exists
if (-not (Test-Path "data/neighborhood_bbs.db")) {
    Write-Host "⚠️  Database not found!" -ForegroundColor $warning
    Write-Host "   Initializing database..." -ForegroundColor Gray
    python scripts/init-db-local.py | Out-Null
    Write-Host "✓ Database initialized" -ForegroundColor $success
}

# Set network binding if requested
if ($Network) {
    $BindHost = "0.0.0.0"
    Write-Host "🌐 Network binding enabled (accept external connections)" -ForegroundColor $warning
    Write-Host "   Find your IP: ipconfig" -ForegroundColor Gray
    Write-Host ""
}

# Prepare environment variables
$env:FLASK_APP = "src/main.py"
$env:FLASK_ENV = "development"
if ($NoDebug) {
    $env:FLASK_DEBUG = "False"
    Write-Host "🔧 Debug mode disabled" -ForegroundColor $warning
} else {
    $env:FLASK_DEBUG = "True"
    Write-Host "🔧 Debug mode enabled (auto-reload on file changes)" -ForegroundColor $info
}

Write-Host ""
Write-Host "🚀 Starting Neighborhood BBS..." -ForegroundColor $success
Write-Host "   Host: $BindHost" -ForegroundColor Gray
Write-Host "   Port: $Port" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================" -ForegroundColor $info
Write-Host "✓ Server running!" -ForegroundColor $success
Write-Host ""
Write-Host "📖 Access here:" -ForegroundColor $info
if ($BindHost -eq "0.0.0.0") {
    $ipaddr = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" }).IPAddress | Select-Object -First 1
    Write-Host "   Local:    http://127.0.0.1:$Port" -ForegroundColor $success
    Write-Host "   Network:  http://$($ipaddr):$Port" -ForegroundColor $success
} else {
    Write-Host "   http://$BindHost`:$Port" -ForegroundColor $success
}
Write-Host ""
Write-Host "🔐 Admin panel:" -ForegroundColor $info
Write-Host "   http://$BindHost`:$Port/admin/login" -ForegroundColor $success
Write-Host ""
Write-Host "📊 API docs:" -ForegroundColor $info
Write-Host "   http://$BindHost`:$Port/api/docs" -ForegroundColor $success
Write-Host ""
Write-Host "⏹️  Press CTRL+C to stop the server" -ForegroundColor $warning
Write-Host "================================================" -ForegroundColor $info
Write-Host ""

# Run the Flask development server
$args = @("src/main.py", "--host", $BindHost, "--port", $Port)
if ($NoDebug) {
    $args += "--no-debug"
}
python @args

# Cleanup
Write-Host ""
Write-Host "🛑 Server stopped." -ForegroundColor $warning
