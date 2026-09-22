@echo off
title UniAssist AI - Stopping Services
color 0C

echo ================================================================
echo               Stopping UniAssist AI Services
echo ================================================================
echo.

echo Stopping Node / Vite frontend processes...
taskkill /F /IM node.exe 2>nul

echo Stopping Python / Uvicorn backend processes...
taskkill /F /FI "WINDOWTITLE eq UniAssist AI - Backend*" /T 2>nul
taskkill /F /IM uvicorn.exe 2>nul

echo.
echo ================================================================
echo   All UniAssist AI services have been stopped.
echo ================================================================
echo.
pause
