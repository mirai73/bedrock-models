#!/bin/bash
# Simple script to serve the site locally for testing

echo "Starting local development server..."
echo "Open http://localhost:8000 in your browser"
echo "Press Ctrl+C to stop"
echo ""

python3 -m http.server 8000
