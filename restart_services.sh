#!/bin/bash
# Wait for previous install (simple heuristic)
echo "⏳ Waiting for environment setup..."
sleep 45 

echo "🛑 Stopping old services..."
pkill -f uvicorn
pkill -f rq

echo "🚀 Starting new services (Python 3.14 via venv)..."
source backend/venv/bin/activate

# Start Uvicorn
nohup uvicorn backend.main:app --reload > uvicorn.log 2>&1 &
echo "✅ Backend started"

# Start Worker
nohup ./start_worker.sh > worker.log 2>&1 &
echo "✅ Worker started"
