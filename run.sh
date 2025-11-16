#!/bin/bash
# Quick start script for Green SME Compliance Co-Pilot

set -e

# Activate virtual environment
if [ -d "green-agent-env" ]; then
    source green-agent-env/bin/activate
else
    echo "Error: Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check database
if [ ! -f "db.sqlite" ]; then
    echo "Database not found. Initializing..."
    python db_init.py
fi

# Start FastAPI server
echo "Starting Green SME Compliance Co-Pilot..."
echo "API: http://localhost:${APP_PORT:-8000}"
echo "Docs: http://localhost:${APP_PORT:-8000}/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py
