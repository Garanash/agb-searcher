#!/bin/bash

# Switch AGB Searcher configuration
# Usage: ./switch-config.sh [nginx|direct]

set -e

CONFIG=${1:-nginx}

echo "🔧 Switching AGB Searcher to $CONFIG configuration..."

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.nginx.yml down 2>/dev/null || true

if [ "$CONFIG" = "nginx" ]; then
    echo "🌐 Starting with Nginx reverse proxy (port 80)..."
    docker-compose -f docker-compose.nginx.yml up --build -d
    echo ""
    echo "✅ Application is now available at:"
    echo "  🌐 Frontend: http://188.225.56.200"
    echo "  🔧 Backend API: http://188.225.56.200/api"
    echo "  ❤️ Health Check: http://188.225.56.200/health"
elif [ "$CONFIG" = "direct" ]; then
    echo "🔗 Starting with direct port access..."
    docker-compose up --build -d
    echo ""
    echo "✅ Application is now available at:"
    echo "  🌐 Frontend: http://188.225.56.200:3000"
    echo "  🔧 Backend API: http://188.225.56.200:8000"
    echo "  ❤️ Health Check: http://188.225.56.200:8000/health"
else
    echo "❌ Invalid configuration. Use 'nginx' or 'direct'"
    exit 1
fi

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Checking service status..."
if [ "$CONFIG" = "nginx" ]; then
    docker-compose -f docker-compose.nginx.yml ps
else
    docker-compose ps
fi

echo ""
echo "🎯 Configuration switched to: $CONFIG"
