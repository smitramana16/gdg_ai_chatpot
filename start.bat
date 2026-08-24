@echo off
title GDG On Campus AI Chatbot - 1-Click Launcher
cls

echo ====================================================================
echo   🤖 GDG On Campus AI Chatbot & Admin Dashboard - 1-Click Setup
echo ====================================================================
echo.

:: Step 1: Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo.
    echo Please install Python 3.10 or higher from:
    echo 👉 https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

:: Step 2: Create Virtual Environment if it does not exist
if not exist "venv\" (
    echo [*] Creating virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [✓] Virtual environment created successfully.
)

:: Step 3: Activate Virtual Environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

:: Step 4: Install/Verify Required Packages
echo [*] Checking and installing Python dependencies from requirements.txt...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Failed to install some dependencies. Trying direct install...
    python -m pip install fastapi uvicorn pydantic python-dotenv
)
echo [✓] Dependencies verified.

:: Step 5: Open Browser in 2 Seconds
echo [*] Opening application in browser at http://localhost:8000 ...
start "" "http://localhost:8000"

:: Step 6: Start Python Backend Server
echo.
echo ====================================================================
echo   ✅ Server is running! Keep this window open.
echo   📍 Web App URL: http://localhost:8000
echo ====================================================================
echo.

python run.py

pause
