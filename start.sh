#!/bin/bash

# Startup script for Green SME Compliance Co-Pilot

echo "Starting Green SME Compliance Co-Pilot..."

# Activate virtual environment if it exists
if [ -d "green-agent-env" ]; then
    source green-agent-env/bin/activate
fi

# Check if database exists, initialize if not
if [ ! -f "db.sqlite" ]; then
    echo "Initializing database..."
    python db_init.py
fi

# Create necessary directories
mkdir -p outputs templates data config

# Start FastAPI server
echo "Starting FastAPI server on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
