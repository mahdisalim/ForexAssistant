# Forex Analysis Assistant - Windows VPS Installation Script
# Run as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Forex Analysis Assistant - Windows Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    exit 1
}

# Variables
$ProjectPath = "C:\ForexAssistant"
$PythonVersion = "3.11"
$MT5InstallerUrl = "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"

# Step 1: Install Python if not present
Write-Host "`n[1/6] Checking Python installation..." -ForegroundColor Yellow
$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonInstalled) {
    Write-Host "Installing Python $PythonVersion..." -ForegroundColor Yellow
    winget install Python.Python.$PythonVersion --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "Python already installed: $(python --version)" -ForegroundColor Green
}

# Step 2: Create project directory
Write-Host "`n[2/6] Setting up project directory..." -ForegroundColor Yellow
if (-not (Test-Path $ProjectPath)) {
    New-Item -ItemType Directory -Path $ProjectPath -Force | Out-Null
}

# Step 3: Create virtual environment
Write-Host "`n[3/6] Creating virtual environment..." -ForegroundColor Yellow
Set-Location $ProjectPath
if (-not (Test-Path "$ProjectPath\venv")) {
    python -m venv venv
}

# Activate venv
& "$ProjectPath\venv\Scripts\Activate.ps1"

# Step 4: Install dependencies
Write-Host "`n[4/6] Installing Python dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install requests beautifulsoup4 lxml httpx pandas python-dateutil openai fastapi uvicorn jinja2 python-dotenv pydantic aiohttp schedule cachetools MetaTrader5

# Step 5: Download and install MetaTrader 5
Write-Host "`n[5/6] MetaTrader 5 Setup..." -ForegroundColor Yellow
$mt5Installed = Test-Path "C:\Program Files\MetaTrader 5\terminal64.exe"
if (-not $mt5Installed) {
    Write-Host "Downloading MetaTrader 5..." -ForegroundColor Yellow
    $mt5Installer = "$env:TEMP\mt5setup.exe"
    Invoke-WebRequest -Uri $MT5InstallerUrl -OutFile $mt5Installer
    Write-Host "Please install MetaTrader 5 manually from: $mt5Installer" -ForegroundColor Cyan
    Start-Process $mt5Installer -Wait
} else {
    Write-Host "MetaTrader 5 already installed" -ForegroundColor Green
}

# Step 6: Create Windows Task Scheduler job
Write-Host "`n[6/6] Setting up scheduled task..." -ForegroundColor Yellow

$taskName = "ForexAssistantScheduler"
$taskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if (-not $taskExists) {
    $action = New-ScheduledTaskAction -Execute "$ProjectPath\venv\Scripts\python.exe" -Argument "$ProjectPath\scheduler.py" -WorkingDirectory $ProjectPath
    $trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Forex Analysis Assistant - Daily Analysis"
    Write-Host "Scheduled task created: $taskName" -ForegroundColor Green
} else {
    Write-Host "Scheduled task already exists" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Copy your project files to: $ProjectPath" -ForegroundColor White
Write-Host "2. Create .env file with your OpenAI API key" -ForegroundColor White
Write-Host "3. Configure MT5 credentials in .env" -ForegroundColor White
Write-Host "4. Run: python main.py" -ForegroundColor White
