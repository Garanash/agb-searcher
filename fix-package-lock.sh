#!/bin/bash

# Fix package-lock.json issues on server
# Usage: ./fix-package-lock.sh

set -e

echo "🔧 Fixing package-lock.json issues..."

# Navigate to frontend directory
cd frontend

# Remove problematic files
echo "🧹 Cleaning up old files..."
rm -rf node_modules
rm -f package-lock.json

# Install dependencies fresh
echo "📦 Installing dependencies..."
npm install

# Verify installation
echo "✅ Verifying installation..."
npm list react-markdown
npm list remark-gfm

echo "🎉 Package-lock.json fixed successfully!"
echo ""
echo "Now you can run:"
echo "  docker-compose -f docker-compose.prod.yml up --build -d"
