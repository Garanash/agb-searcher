#!/bin/bash

# Fix npm registry issues on server
# Usage: ./fix-npm-registry.sh

set -e

echo "🔧 Fixing npm registry issues..."

# Check current npm registry
echo "📋 Current npm registry:"
npm config get registry

# Set correct npm registry
echo "🔧 Setting npm registry to official registry..."
npm config set registry https://registry.npmjs.org/

# Verify registry change
echo "✅ New npm registry:"
npm config get registry

# Clear npm cache
echo "🧹 Clearing npm cache..."
npm cache clean --force

# Test npm connectivity
echo "🌐 Testing npm connectivity..."
npm ping

echo "✅ npm registry fixed successfully!"
echo ""
echo "Now you can run:"
echo "  docker-compose up --build"
echo "  # or"
echo "  docker-compose -f docker-compose.prod.yml up --build -d"
