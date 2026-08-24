@echo off
title GDG On Campus AI Chatbot Launcher
cls
echo ============================================================
echo   🤖 Starting GDG On Campus AI Chatbot & Admin Dashboard...
echo ============================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Python is not found on this system.
    echo [!] Opening web page directly...
    start index.html
    pause
    exit /b
)

echo [*] Checking & Installing dependencies (FastAPI, Uvicorn)...
python -c "import fastapi, uvicorn" >nul 2>nul
if %errorlevel% neq 0 (
    echo [*] Installing required packages...
    python -m pip install fastapi uvicorn pydantic
)

echo [*] Launching AI Backend Server on http://localhost:8000 ...
start /b python run.py >nul 2>&1

timeout /t 2 >nul
echo [*] Opening Web Application in Browser...
start http://localhost:8000

echo.
echo ============================================================
echo   ✅ Chatbot is active! You can minimize this window.
echo ============================================================
echo.
pause
