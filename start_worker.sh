#!/bin/bash
# Start the RQ Worker ensuring the backend module is in path
export PYTHONPATH=$PYTHONPATH:$(pwd)
echo "🚀 Starting Gravity Worker (Queues: default, analysis, render)..."
rq worker default analysis render
