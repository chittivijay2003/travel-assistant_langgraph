#!/bin/bash

# ============================================
# PRODUCTION DEPLOYMENT SCRIPT
# ============================================

set -e  # Exit on error

echo "=========================================="
echo "🚀 Travel Assistant - Production Deploy"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your GOOGLE_API_KEY"
    exit 1
fi

# Check if GOOGLE_API_KEY is set
if grep -q "your_google_api_key_here" .env; then
    echo "❌ Error: GOOGLE_API_KEY not configured in .env"
    echo "📝 Please edit .env and add your actual API key"
    exit 1
fi

echo "✅ Environment configuration validated"

# Build Docker image
echo ""
echo "🔨 Building Docker image..."
docker-compose build

# Start services
echo ""
echo "🚀 Starting services..."
docker-compose up -d

# Wait for service to be healthy
echo ""
echo "⏳ Waiting for service to be healthy..."
sleep 5

# Check health
echo ""
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Service is healthy!"
else
    echo "❌ Service health check failed"
    docker-compose logs travel-assistant
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Deployment successful!"
echo "=========================================="
echo ""
echo "📍 API Endpoint: http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 View logs: docker-compose logs -f travel-assistant"
echo "🛑 Stop: docker-compose down"
echo ""
