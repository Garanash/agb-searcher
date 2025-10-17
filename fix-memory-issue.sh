#!/bin/bash

# Fix memory issues during React build
# Usage: ./fix-memory-issue.sh

set -e

echo "🔧 Fixing memory issues during React build..."

# Check available memory
echo "📊 Checking system memory..."
free -h

# Check Docker memory limits
echo "🐳 Checking Docker memory limits..."
docker system info | grep -i memory || echo "No specific memory limits found"

# Clean up Docker to free memory
echo "🧹 Cleaning up Docker..."
docker system prune -f

# Build with increased memory
echo "🚀 Building with increased memory limits..."

# Option 1: Build with memory-optimized Dockerfile
echo "Building with memory-optimized Dockerfile..."
docker-compose -f docker-compose.prod.yml build --no-cache frontend

# If that fails, try alternative approach
if [ $? -ne 0 ]; then
    echo "⚠️ First build failed, trying alternative approach..."
    
    # Build frontend separately with more memory
    cd frontend
    docker build -f Dockerfile.prod.memory --build-arg NODE_OPTIONS="--max-old-space-size=6144" -t agb-searcher-frontend-memory .
    cd ..
    
    # Update docker-compose to use the built image
    docker-compose -f docker-compose.prod.yml up -d frontend
fi

echo "✅ Memory optimization completed!"
echo ""
echo "To check if it worked:"
echo "  docker-compose -f docker-compose.prod.yml ps"
echo "  curl -I http://localhost"
