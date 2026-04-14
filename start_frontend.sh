#!/bin/bash

# Script to start the frontend server

cd frontend

# Check if Python is available
if command -v python3 &> /dev/null; then
    echo "Starting frontend server on http://localhost:8080"
    python3 -m http.server 8080
elif command -v python &> /dev/null; then
    echo "Starting frontend server on http://localhost:8080"
    python -m http.server 8080
else
    echo "Python not found. Please install Python or use another HTTP server."
    echo "You can also use: npx http-server frontend -p 8080"
    exit 1
fi

