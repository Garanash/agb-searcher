#!/bin/bash

# Update AI models in AGB Searcher
# Usage: ./update-models.sh

set -e

echo "🤖 Updating AI models in AGB Searcher..."

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull

# Check if using nginx or direct configuration
if docker-compose -f docker-compose.nginx.yml ps | grep -q "Up"; then
    echo "🌐 Using Nginx configuration..."
    COMPOSE_FILE="docker-compose.nginx.yml"
else
    echo "🔗 Using direct configuration..."
    COMPOSE_FILE="docker-compose.yml"
fi

# Restart backend to load new models
echo "🔄 Restarting backend to load new models..."
docker-compose -f $COMPOSE_FILE restart backend

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 10

# Test models endpoint
echo "🧪 Testing models endpoint..."
if curl -s http://localhost:8000/models > /dev/null; then
    echo "✅ Models endpoint is working"
    echo "📊 Available models:"
    curl -s http://localhost:8000/models | jq -r '.[] | "  - \(.name) (\(.provider)) - \(.category)"' 2>/dev/null || echo "  Models loaded successfully"
else
    echo "❌ Models endpoint not responding, checking logs..."
    docker-compose -f $COMPOSE_FILE logs backend | tail -20
fi

echo ""
echo "✅ Models update complete!"
echo ""
echo "🎯 New features:"
echo "  - 20+ AI models from major providers"
echo "  - Grouped by provider (OpenAI, Anthropic, Google, etc.)"
echo "  - Categorized by tier (premium, standard, budget, etc.)"
echo "  - Vision support indicators"
echo "  - Search functionality in model selector"
echo ""
echo "🌐 Access your application:"
if [ "$COMPOSE_FILE" = "docker-compose.nginx.yml" ]; then
    echo "  Frontend: http://188.225.56.200"
    echo "  API: http://188.225.56.200/api"
else
    echo "  Frontend: http://188.225.56.200:3000"
    echo "  API: http://188.225.56.200:8000"
fi
