#!/usr/bin/env bash
# UniAssist AI - Local Development Startup Script (Bash)
set -e

echo "=========================================================="
echo "       Starting UniAssist AI Local Development Environment "
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "[1/2] Starting FastAPI Backend on port 8000..."
source backend/.venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "[2/2] Starting React Frontend on port 5173..."
cd frontend
npm run dev

trap "kill $BACKEND_PID" EXIT
