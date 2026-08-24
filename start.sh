#!/bin/bash
echo "============================================================"
echo "  🤖 Starting GDG On Campus AI Chatbot & Admin Dashboard..."
echo "============================================================"
echo ""
echo "Opening browser at http://localhost:8000 ..."
sleep 1
open http://localhost:8000 2>/dev/null || xdg-open http://localhost:8000 2>/dev/null || true
echo ""
echo "Running Python Server..."
python3 run.py
