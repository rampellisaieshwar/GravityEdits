#!/bin/bash
# Start the RQ Worker ensuring the backend module is in path
# Check if venv exists (Local Dev)
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
fi

export PYTHONPATH=$PYTHONPATH:$(pwd)
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

echo "🚀 Starting Gravity Worker (Queues: default, analysis, render, videodb)..."

# Determine python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

rq worker default analysis render videodb
