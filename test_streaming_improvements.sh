#!/bin/bash

echo "🧪 Testing Improved Streaming Response"
echo "========================================"
echo ""
echo "Query: Plan a 3-day trip to Tokyo from Singapore. Search flights, check weather, and find attractions."
echo ""
echo "Streaming response (watch the delays and step-by-step execution):"
echo "-------------------------------------------------------------------"
echo ""

curl -N -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a 3-day trip to Tokyo from Singapore. Search flights, check weather, and find attractions.",
    "stream": true
  }'

echo ""
echo ""
echo "✅ Test completed!"
