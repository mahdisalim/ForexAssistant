@echo off
title Forex Analysis Assistant
echo ========================================
echo   Forex Analysis Assistant - Startup
echo ========================================
echo.

cd /d %~dp0..

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Check if .env exists
if not exist ".env" (
    echo.
    echo ERROR: .env file not found!
    echo Please create .env file from .env.example
    echo.
    pause
    exit /b 1
)

:: Start services
echo.
echo Starting services...
echo.

:: Start web server in new window
start "Forex Web Server" cmd /k "cd /d %~dp0.. && venv\Scripts\activate && python main.py"

:: Wait a bit
timeout /t 3 /nobreak > nul

:: Start monitor in new window
start "Forex Monitor" cmd /k "cd /d %~dp0.. && venv\Scripts\activate && python deploy\monitor.py"

:: Wait a bit
timeout /t 2 /nobreak > nul

:: Start trading bot
echo.
echo Starting Trading Bot...
echo Press Ctrl+C to stop
echo.
python trading_bot.py
