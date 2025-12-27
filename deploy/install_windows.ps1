# Forex Analysis Assistant - Windows VPS Installation Script
# Run as Administrator
# Usage: .\deploy\install_windows.ps1
# Note: Run this from the project root or deploy folder

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Forex Analysis Assistant - Windows Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    exit 1
}

# Variables - Use current script location (parent of deploy folder)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectPath = Split-Path -Parent $ScriptDir
$PythonVersion = "3.11"
$MT5InstallerUrl = "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"

Write-Host "Project Path: $ProjectPath" -ForegroundColor Cyan

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

# Step 2: Verify project directory exists
Write-Host "`n[2/6] Verifying project directory..." -ForegroundColor Yellow
if (-not (Test-Path $ProjectPath)) {
    Write-Host "ERROR: Project directory not found: $ProjectPath" -ForegroundColor Red
    Write-Host "Please run this script from the deploy folder inside your project." -ForegroundColor Red
    exit 1
}
Write-Host "Project directory verified: $ProjectPath" -ForegroundColor Green

# Step 3: Create virtual environment
Write-Host "`n[3/6] Creating virtual environment..." -ForegroundColor Yellow
Set-Location $ProjectPath
if (-not (Test-Path "$ProjectPath\venv")) {
    python -m venv venv
}

# Activate venv
& "$ProjectPath\venv\Scripts\Activate.ps1"

# Step 4: Install dependencies from requirements.txt
Write-Host "`n[4/6] Installing Python dependencies..." -ForegroundColor Yellow

# Upgrade pip first
python -m pip install --upgrade pip

# Try installing from requirements.txt
# If PyPI is blocked, user can use a mirror
Write-Host "Installing from requirements.txt..." -ForegroundColor Yellow
pip install -r "$ProjectPath\requirements.txt" 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyPI connection failed. Trying alternative mirror..." -ForegroundColor Yellow
    pip install -r "$ProjectPath\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Could not install all dependencies." -ForegroundColor Red
        Write-Host "Please check your internet connection or use a VPN." -ForegroundColor Red
        Write-Host "You can manually install with: pip install -r requirements.txt" -ForegroundColor Yellow
    }
}

# Step 5: Download and install MetaTrader 5
Write-Host "`n[5/6] MetaTrader 5 Setup..." -ForegroundColor Yellow
# Check common MT5 installation paths
$mt5Paths = @(
    "C:\Program Files\MetaTrader 5\terminal64.exe",
    "C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
    "$env:LOCALAPPDATA\Programs\MetaTrader 5\terminal64.exe"
)
$mt5Installed = $false
foreach ($path in $mt5Paths) {
    if (Test-Path $path) {
        $mt5Installed = $true
        Write-Host "MetaTrader 5 found at: $path" -ForegroundColor Green
        break
    }
}
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
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Forex Analysis Assistant - Daily Analysis" -User "SYSTEM" -RunLevel Highest
    Write-Host "Scheduled task created: $taskName" -ForegroundColor Green
} else {
    Write-Host "Scheduled task already exists" -ForegroundColor Green
}

# Step 7: Create .env file if not exists
Write-Host "`n[7/7] Setting up environment file..." -ForegroundColor Yellow
if (-not (Test-Path "$ProjectPath\.env")) {
    if (Test-Path "$ProjectPath\.env.example") {
        Copy-Item "$ProjectPath\.env.example" "$ProjectPath\.env"
        Write-Host ".env file created from .env.example" -ForegroundColor Green
        Write-Host "Please edit .env and add your API keys!" -ForegroundColor Yellow
    } else {
        Write-Host "WARNING: .env.example not found" -ForegroundColor Red
    }
} else {
    Write-Host ".env file already exists" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nProject installed at: $ProjectPath" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file and add your OpenAI API key" -ForegroundColor White
Write-Host "2. Configure MT5 credentials in .env" -ForegroundColor White
Write-Host "3. Activate venv: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "4. Run: python main.py" -ForegroundColor White
Write-Host "`nOr use: deploy\start_all.bat" -ForegroundColor Cyan
