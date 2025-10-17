#!/bin/bash

# Build React app on host machine to avoid Docker memory issues
# Usage: ./build-on-host.sh

set -e

echo "🏗️ Building React app on host machine..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Installing Node.js 18..."
    
    # Install Node.js 18
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    echo "✅ Node.js installed successfully"
fi

# Check Node.js version
echo "📋 Node.js version: $(node --version)"
echo "📋 npm version: $(npm --version)"

# Navigate to frontend directory
cd frontend

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf build node_modules package-lock.json

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build with increased memory
echo "🔨 Building React app with increased memory..."
NODE_OPTIONS="--max-old-space-size=4096" npm run build

# Check if build was successful
if [ -d "build" ]; then
    echo "✅ Build completed successfully!"
    echo "📁 Build directory size: $(du -sh build | cut -f1)"
else
    echo "❌ Build failed!"
    exit 1
fi

# Go back to root directory
cd ..

echo "🎉 Host build completed successfully!"
echo ""
echo "Now you can run:"
echo "  docker-compose -f docker-compose.minimal.yml up -d"
