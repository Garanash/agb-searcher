# AGB Searcher - Deployment Guide

## Debian Server Deployment

### Prerequisites

1. **Debian 11+** server with root access
2. **Docker** and **Docker Compose** installed
3. **Git** for cloning the repository

### Installation Steps

#### 1. Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply group changes
```

#### 2. Clone and Setup Project

```bash
# Clone repository
git clone <your-repo-url>
cd agb-searcher

# Copy environment file
cp env.example .env

# Edit environment variables
nano .env
```

#### 3. Configure Environment Variables

Edit `.env` file with your actual values:

```env
# Database configuration
POSTGRES_PASSWORD=your_secure_password_here

# Polza.AI API configuration
POLZA_API_KEY=your_polza_api_key_here

# Application URLs
REACT_APP_API_URL=http://localhost:8000
```

#### 4. Deploy Application

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Manual Deployment (Alternative)

If you prefer manual deployment:

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up --build -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Service Management

#### Start Services
```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

#### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

#### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up --build -d
```

### Service URLs

After successful deployment:

- **Frontend**: http://your-server-ip
- **Backend API**: http://your-server-ip:8000
- **API Documentation**: http://your-server-ip:8000/docs

### Security Considerations

1. **Change default passwords** in `.env` file
2. **Use HTTPS** in production (configure nginx with SSL)
3. **Firewall configuration**:
   ```bash
   # Allow only necessary ports
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS (if using SSL)
   sudo ufw enable
   ```

### Troubleshooting

#### Check Service Status
```bash
docker-compose -f docker-compose.prod.yml ps
```

#### Check Logs
```bash
docker-compose -f docker-compose.prod.yml logs
```

#### Restart Specific Service
```bash
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart frontend
```

#### Database Backup
```bash
# Create backup
docker exec agb-searcher-postgres-prod pg_dump -U agb_user agb_searcher > backup.sql

# Restore backup
docker exec -i agb-searcher-postgres-prod psql -U agb_user agb_searcher < backup.sql
```

### Performance Optimization

1. **Increase Docker resources** if needed
2. **Configure nginx caching** for static assets
3. **Monitor resource usage**:
   ```bash
   docker stats
   ```

### SSL/HTTPS Setup (Optional)

For production with SSL:

1. Obtain SSL certificates (Let's Encrypt recommended)
2. Update nginx configuration
3. Modify docker-compose.prod.yml to expose port 443
4. Update REACT_APP_API_URL to use HTTPS
