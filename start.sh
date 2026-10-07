#!/usr/bin/env bash

# Resolve project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "🚀 Starting Signal Clone Fullstack Platform..."
echo "=================================================="

# Function to shut down background jobs on exit/Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 0. Start Microservices Database & Broker Tier
echo "🐘 [*] Ensuring PostgreSQL and Redis are running..."
docker compose up -d postgres redis 2>/dev/null

# 1. Start Backend Server
echo "📦 [1/2] Starting Backend (FastAPI on port 8000)..."
cd "$SCRIPT_DIR/backend"

if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON_EXEC=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_EXEC=".venv/bin/python"
elif command -v python &> /dev/null; then
    PYTHON_EXEC="python"
elif command -v python3 &> /dev/null; then
    PYTHON_EXEC="python3"
else
    echo "❌ Error: Python not found!"
    exit 1
fi

"$PYTHON_EXEC" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 2. Start Frontend Server
echo "🌐 [2/2] Starting Frontend (Vite on port 8443)..."
cd "$SCRIPT_DIR/frontend"

if command -v npm &> /dev/null; then
    npm run dev &
    FRONTEND_PID=$!
else
    echo "❌ Error: npm not found!"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ Both services are up and running!"
echo "   - Frontend: http://localhost:8443"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "=================================================="
echo "Press Ctrl+C to stop all services."
echo ""

# Wait for background jobs
wait
