@echo off
title UniAssist AI - Starting Services
color 0B

echo ================================================================
echo               Starting UniAssist AI Platform
echo ================================================================
echo.
echo [1/3] Launching FastAPI Backend on http://localhost:8000 ...
start "UniAssist AI - Backend (Port 8000)" cmd /k "cd /d %~dp0backend && if exist .venv\Scripts\python.exe (.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000) else (python -m uvicorn app.main:app --reload --port 8000)"

echo.
echo [2/3] Launching React Vite Frontend on http://localhost:5173 ...
start "UniAssist AI - Frontend (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo [3/3] Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

echo.
echo Opening UniAssist AI in your default browser...
start http://localhost:5173

echo.
echo ================================================================
echo   Services are running in their respective console windows:
echo   - Backend API:  http://localhost:8000 (Swagger docs: /docs)
echo   - Frontend App: http://localhost:5173
echo.
echo   To stop the services, close both console windows or run stop.bat
echo ================================================================
echo.
pause
