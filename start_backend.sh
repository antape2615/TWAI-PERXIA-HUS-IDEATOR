#!/bin/bash

# Script to start the backend server

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Please create one from .env.example"
fi

# Check if requirements are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Start the backend server
cd backend
python3 main.py

