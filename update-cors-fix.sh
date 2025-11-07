#!/bin/bash

# Update and restart AGB Searcher with CORS fixes
# Usage: ./update-cors-fix.sh

set -e

echo "🔧 Updating AGB Searcher with CORS fixes..."

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Rebuild and start containers
echo "🚀 Rebuilding and starting containers..."
docker-compose up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker-compose ps

# Test API connectivity
echo "🌐 Testing API connectivity..."
curl -I http://localhost:8000/health || echo "Backend not ready yet"

echo "✅ Update complete!"
echo ""
echo "🌐 Access your application:"
echo "  Frontend: http://188.225.56.200:3000"
echo "  Backend API: http://188.225.56.200:8000"
echo "  Health Check: http://188.225.56.200:8000/health"
echo ""
echo "📋 If you still see CORS errors, wait a few minutes for the containers to fully start."
