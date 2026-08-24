@echo off
title GDG On Campus AI Chatbot Launcher
cls
echo ============================================================
echo   🤖 Starting GDG On Campus AI Chatbot & Admin Dashboard...
echo ============================================================
echo.
echo Opening browser at http://localhost:8000 ...
timeout /t 2 >nul
start http://localhost:8000
echo.
echo Running Python Server (Do not close this window)...
python run.py
pause
