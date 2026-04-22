@echo off
title Defense Hackathon - Backend Server
color 0A

echo ============================================
echo   Defense Hackathon 2026 - Backend Startup
echo ============================================
echo.

:: ── Navigate to backend folder ─────────────────────────────────────────────
cd /d "%~dp0backend"

:: ── Upgrade pip / setuptools / wheel first ─────────────────────────────────
echo [1/3] Upgrading pip, setuptools and wheel...
python -m pip install --upgrade pip setuptools wheel
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to upgrade pip. Make sure Python is installed and on PATH.
    pause
    exit /b 1
)

:: ── Install project dependencies ───────────────────────────────────────────
echo.
echo [2/3] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Dependency installation failed. Check the output above.
    pause
    exit /b 1
)

:: ── Start the FastAPI server ───────────────────────────────────────────────
echo.
echo [3/3] Starting FastAPI backend server...
echo       API will be available at: http://localhost:8000
echo       Docs available at:        http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server.
echo.
python run.py

pause
