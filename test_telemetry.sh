#!/bin/bash
# Test script to simulate multiple agents

echo "🧪 Testing Telemetry System"
echo "==========================="
echo ""

# Start server in background
echo "Starting telemetry server..."
python3 telemetry_server.py > telemetry.log 2>&1 &
SERVER_PID=$!

echo "Server PID: $SERVER_PID"
echo "Waiting for server to start..."
sleep 3

# Check if server is running
if ! curl -s http://localhost:8888/api/stats > /dev/null; then
    echo "❌ Server failed to start. Check telemetry.log"
    cat telemetry.log
    exit 1
fi

echo "✅ Server running"
echo ""

# Register a test agent
echo "📡 Registering test agent..."
python3 agent_telemetry.py

echo ""
echo "📊 Current Stats:"
curl -s http://localhost:8888/api/stats | python3 -m json.tool

echo ""
echo "✅ Test complete!"
echo ""
echo "Dashboard: http://localhost:8888"
echo ""
echo "To stop server: kill $SERVER_PID"
echo "Or: pkill -f telemetry_server.py"

