#!/bin/bash

# Complete solution for memory issues during React build
# Usage: ./solve-memory-issues.sh

set -e

echo "🔧 Solving React build memory issues..."

# Check available memory
echo "📊 Checking system memory..."
free -h

# Check if we have enough memory (at least 2GB)
TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
if [ $TOTAL_MEM -lt 2048 ]; then
    echo "⚠️ Low memory detected ($TOTAL_MEM MB). Creating swap file..."
    
    # Create swap file if it doesn't exist
    if [ ! -f /swapfile ]; then
        echo "Creating 2GB swap file..."
        sudo fallocate -l 2G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        
        # Make it permanent
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
        echo "✅ Swap file created and activated"
    else
        echo "✅ Swap file already exists"
    fi
fi

# Clean up Docker
echo "🧹 Cleaning up Docker..."
docker system prune -f

# Try different build approaches
echo "🚀 Trying different build approaches..."

# Approach 1: Build on host machine
echo "📦 Approach 1: Building on host machine..."
if command -v node &> /dev/null; then
    echo "Node.js found, building on host..."
    chmod +x build-on-host.sh
    ./build-on-host.sh
    
    if [ -d "frontend/build" ]; then
        echo "✅ Host build successful! Using minimal Docker setup..."
        docker-compose -f docker-compose.minimal.yml up --build -d
        echo "🎉 Application started with minimal Docker setup!"
        exit 0
    fi
else
    echo "Node.js not found, skipping host build..."
fi

# Approach 2: Try with maximum memory allocation
echo "📦 Approach 2: Docker build with maximum memory..."
docker-compose -f docker-compose.prod.yml build --no-cache frontend

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
    docker-compose -f docker-compose.prod.yml up -d
    echo "🎉 Application started with Docker build!"
    exit 0
fi

# Approach 3: Multi-stage build with memory optimization
echo "📦 Approach 3: Multi-stage build with memory optimization..."
cd frontend

# Create ultra-minimal Dockerfile
cat > Dockerfile.ultra << EOF
# Stage 1: Build with maximum memory
FROM node:18-alpine as builder

# Set maximum memory
ENV NODE_OPTIONS="--max-old-space-size=6144"
ENV GENERATE_SOURCEMAP=false

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install only production dependencies first
RUN npm install --only=production

# Copy source and install dev dependencies
COPY . .
RUN npm install

# Build with memory optimization
RUN npm run build

# Stage 2: Minimal nginx
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# Build with ultra-minimal approach
docker build -f Dockerfile.ultra -t agb-searcher-frontend-ultra .

if [ $? -eq 0 ]; then
    echo "✅ Ultra-minimal build successful!"
    cd ..
    
    # Update docker-compose to use the built image
    cat > docker-compose.ultra.yml << EOF
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: agb-searcher-postgres-ultra
    environment:
      POSTGRES_DB: agb_searcher
      POSTGRES_USER: agb_user
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - agb_network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: agb-searcher-backend-ultra
    environment:
      - DATABASE_URL=postgresql://agb_user:\${POSTGRES_PASSWORD}@postgres:5432/agb_searcher
      - POLZA_API_KEY=\${POLZA_API_KEY}
      - REACT_APP_API_URL=http://localhost:8000
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - agb_network

  frontend:
    image: agb-searcher-frontend-ultra
    container_name: agb-searcher-frontend-ultra
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - agb_network

volumes:
  postgres_data:

networks:
  agb_network:
    driver: bridge
EOF
    
    docker-compose -f docker-compose.ultra.yml up -d
    echo "🎉 Application started with ultra-minimal build!"
    exit 0
fi

echo "❌ All build approaches failed. Please check server resources."
echo "💡 Consider:"
echo "  1. Increasing server RAM to at least 4GB"
echo "  2. Using a more powerful server"
echo "  3. Building on a different machine and copying the build"
