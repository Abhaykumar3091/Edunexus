# UniAssist AI - Local Development Startup Script (PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       Starting UniAssist AI Local Development Environment " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$root = $PSScriptRoot | Split-Path
Set-Location $root

# Ensure PATH has node, python uv
$nodeDir = 'C:\Users\arshu\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.19.0-win-x64'
$uvDir = 'C:\Users\arshu\.local\bin'
$pythonDir = 'C:\Users\arshu\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none'
$env:Path = "$pythonDir;$nodeDir;$uvDir;$env:Path"

Write-Host "`n[1/3] Checking environment & database..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Gray
    Copy-Item ".env.example" ".env"
}

Write-Host "`n[2/3] Backend starting on http://localhost:8000..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "backend\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn app.main:app --reload --port 8000" -PassThru -NoNewWindow

Write-Host "`n[3/3] Frontend starting on http://localhost:5173..." -ForegroundColor Green
Set-Location "$root\frontend"
& "$nodeDir\npm.cmd" run dev
