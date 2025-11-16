#!/bin/bash
# Quick start script for telemetry monitoring

echo "🚀 Starting Node3 Telemetry Monitoring"
echo "======================================"
echo ""

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required packages..."
    pip3 install --break-system-packages fastapi uvicorn websockets 2>&1 | grep -v "already satisfied" || true
fi

echo ""
echo "✅ Dependencies OK"
echo ""
echo "🌐 Starting telemetry server..."
echo "   Dashboard: http://localhost:8888"
echo "   API: http://localhost:8888/api/stats"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 telemetry_server.py

