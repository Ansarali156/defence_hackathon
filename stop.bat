@echo off
title Defense Hackathon - Stop Server
color 0C

echo ============================================
echo   Defense Hackathon 2026 - Stopping Server
echo ============================================
echo.

:: ── Kill processes listening on port 8000 ─────────────────────────────────
echo [1/2] Stopping FastAPI server on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo        Killing PID %%a ...
    taskkill /PID %%a /F >nul 2>&1
)

:: ── Kill any remaining uvicorn / python run.py processes ──────────────────
echo [2/2] Stopping any remaining uvicorn processes...
taskkill /IM uvicorn.exe /F >nul 2>&1

:: Kill python processes running run.py (best effort)
wmic process where "Name='python.exe' and CommandLine like '%%run.py%%'" delete >nul 2>&1

echo.
echo [DONE] Server stopped successfully.
echo.
pause
