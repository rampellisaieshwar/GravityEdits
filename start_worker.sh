#!/bin/bash
# Start the RQ Worker ensuring the backend module is in path
source backend/venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
echo "🚀 Starting Gravity Worker (Queues: default, analysis, render)..."
rq worker default analysis render videodb
