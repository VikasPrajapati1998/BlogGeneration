# Docker Deployment Guide

> Professional containerized deployment for AI Blog Generator with HITL workflow

## 🎯 Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/VikasPrajapati1998/BlogGeneration.git
cd BlogGeneration
cp .env.example .env  # Edit with your credentials

# 2. Deploy
docker-compose up -d

# 3. Verify
docker-compose ps
curl http://localhost:8000/health

# Access: http://localhost:8000
```

## 📦 Service Architecture

```
┌─────────────────────────────────────────────────┐
│  Docker Compose Stack (bloggeneration)          │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  blog_mysql  │  │  blog_ollama │             │
│  │  Port: 3307  │  │  Port: 11434 │             │
│  │  MySQL 8.0   │  │  LLM Server  │             │
│  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                     │
│         └────────┬────────┘                     │
│                  ↓                              │
│         ┌─────────────────┐                     │
│         │   blog_app      │                     │
│         │   Port: 8000    │                     │
│         │   FastAPI       │                     │
│         └─────────────────┘                     │
│                  ↑                              │
│         ┌─────────────────┐                     │
│         │ ollama-pull     │                     │
│         │ (init service)  │                     │
│         └─────────────────┘                     │
│                                                 │
└─────────────────────────────────────────────────┘

Volumes:
  - mysql_data      → MySQL persistence
  - ollama_data     → Ollama models
  - checkpoint_data → SQLite workflows
```

## 🔧 Services Configuration

### App Service (FastAPI)

```yaml
Ports: 8000:8000
Image: Built from Dockerfile
Depends: mysql, ollama
Health: curl http://localhost:8000/health
Restart: unless-stopped

Volumes:
  - checkpoint_data:/app/data  # SQLite workflow state
  - ./.env:/app/.env:ro        # Environment config (optional)

Environment:
  DB_HOST: mysql               # Container name
  DB_PORT: 3306               # Internal port
  OLLAMA_BASE_URL: http://ollama:11434
```

### MySQL Service

```yaml
Ports: 3307:3306              # External:Internal
Image: mysql:8.0
Health: mysqladmin ping
Restart: unless-stopped

Volumes:
  - mysql_data:/var/lib/mysql
  - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro

Environment:
  MYSQL_ROOT_PASSWORD: ${PASSWORD}
  MYSQL_DATABASE: blog_db
```

### Ollama Service

```yaml
Ports: 11434:11434
Image: ollama/ollama:latest
Health: ollama list
Restart: unless-stopped

Volumes:
  - ollama_data:/root/.ollama  # Model storage (~500MB-4GB)
```

### Ollama-Pull (Init Service)

```yaml
Purpose: Download qwen2.5:0.5b model on first run
Depends: ollama
Restart: no (runs once)
```

## ⚙️ Environment Variables

Create `.env` file:

```env
# Database
DATABASE=blog_db
PASSWORD=secure_password_here
MYSQL_ROOT_PASSWORD=secure_password_here
DB_HOST=mysql                    # Container name
DB_PORT=3306                     # Internal port
DB_USER=root

# LangChain (Optional - for tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=BlogGeneration

# Ollama
OLLAMA_BASE_URL=http://ollama:11434

# Application
DEBUG=false
MAX_CONCURRENT_GENERATIONS=5
```

## 🚀 Common Operations

### Deployment

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d app

# Build and start (after code changes)
docker-compose up --build -d

# Build without cache
docker-compose build --no-cache app
```

### Monitoring

```bash
# View logs (all services)
docker-compose logs -f

# View specific service
docker-compose logs -f app
docker logs blog_app

# Check status
docker-compose ps

# Resource usage
docker stats blog_app blog_mysql blog_ollama
```

### Maintenance

```bash
# Restart service
docker-compose restart app

# Stop all
docker-compose down

# Stop and remove volumes (⚠️ DATA LOSS)
docker-compose down -v

# Update images
docker-compose pull
docker-compose up -d
```

### Database Access

```bash
# MySQL shell
docker-compose exec mysql mysql -u root -p
# Password from .env

# Run SQL query
docker-compose exec mysql mysql -u root -p${PASSWORD} blog_db -e "SELECT COUNT(*) FROM blog_posts;"

# Backup database
docker-compose exec -T mysql mysqldump -u root -p${PASSWORD} blog_db > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T mysql mysql -u root -p${PASSWORD} blog_db
```

### Ollama Management

```bash
# List models
docker-compose exec ollama ollama list

# Pull new model
docker-compose exec ollama ollama pull llama3.2:1b

# Remove model
docker-compose exec ollama ollama rm qwen2.5:0.5b

# Model size check
docker-compose exec ollama du -sh /root/.ollama/models
```

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs for errors
docker-compose logs app

# Common issues:
# 1. Port conflict
netstat -ano | findstr :8000    # Windows
lsof -i :8000                   # Mac/Linux

# 2. Environment variables
docker-compose config           # Validate compose file

# 3. Rebuild
docker-compose down
docker-compose up --build
```

### Database Connection Failed

```bash
# Verify MySQL is healthy
docker-compose ps mysql

# Test connection
docker-compose exec mysql mysql -u root -p

# Check network
docker network inspect bloggeneration_blog_network

# Verify DB_HOST in .env is "mysql" (not "localhost")
```

### Ollama Model Issues

```bash
# Check if model downloaded
docker-compose logs ollama-pull

# Should show: "Model pulled successfully!"

# Manually pull
docker-compose exec ollama ollama pull qwen2.5:0.5b

# Verify
docker-compose exec ollama ollama list

# Restart if needed
docker-compose restart ollama
```

### Workflow State Issues

```bash
# Check SQLite checkpoint volume
docker volume inspect bloggeneration_checkpoint_data

# Access checkpoint database
docker-compose exec app sqlite3 /app/data/blog_workflow.db
sqlite> SELECT thread_id FROM checkpoints;

# Reset checkpoints (⚠️ loses pending workflows)
docker volume rm bloggeneration_checkpoint_data
docker-compose up -d
```

## 📊 Performance Tuning

### Resource Limits

Add to `docker-compose.yml`:

```yaml
app:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        memory: 1G

mysql:
  deploy:
    resources:
      limits:
        memory: 1G

ollama:
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 4G
```

### Volume Performance

```bash
# Check volume usage
docker system df -v

# Cleanup unused volumes
docker volume prune

# Backup before cleanup
docker run --rm -v bloggeneration_checkpoint_data:/data \
  -v $(pwd)/backups:/backup alpine \
  tar czf /backup/checkpoint_backup.tar.gz -C /data .
```

## 🔐 Security Best Practices

### 1. Environment Variables

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use strong passwords
PASSWORD=$(openssl rand -base64 32)
```

### 2. Network Isolation

```yaml
# In docker-compose.yml
networks:
  blog_network:
    driver: bridge
    internal: true  # No external access

services:
  app:
    networks:
      - blog_network
    ports:
      - "8000:8000"  # Only expose necessary ports
```

### 3. Read-Only Mounts

```yaml
volumes:
  - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
  - ./.env:/app/.env:ro
```

## 📦 Multi-Environment Setup

### Development

```bash
# Use docker-compose.override.yml for dev settings
cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  app:
    volumes:
      - .:/app  # Live reload
    environment:
      DEBUG: "true"
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
EOF

docker-compose up
```

### Production

```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# docker-compose.prod.yml example:
services:
  app:
    restart: always
    environment:
      DEBUG: "false"
    deploy:
      replicas: 2
```

## 🔄 CI/CD Integration

### Build & Push

```bash
# Build image
docker build -t blog-generator:latest .

# Tag for registry
docker tag blog-generator:latest registry.example.com/blog-generator:1.0.0

# Push
docker push registry.example.com/blog-generator:1.0.0
```

### Automated Deployment

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        run: |
          docker-compose pull
          docker-compose up -d --build
```

## 📋 Health Checks

### Service Health

```bash
# Check all services
docker-compose ps

# Should show "healthy" status:
# blog_app    ... Up (healthy)
# blog_mysql  ... Up (healthy)
# blog_ollama ... Up (healthy)

# Manual health check
curl http://localhost:8000/health
curl http://localhost:11434/api/tags
```

### Custom Health Script

```bash
#!/bin/bash
# health-check.sh

set -e

# App health
curl -f http://localhost:8000/health || exit 1

# MySQL health
docker-compose exec -T mysql mysqladmin ping -h localhost || exit 1

# Ollama health
curl -f http://localhost:11434/api/tags || exit 1

echo "✓ All services healthy"
```

## 📚 Additional Resources

- **Docker Docs**: https://docs.docker.com/compose/
- **MySQL Image**: https://hub.docker.com/_/mysql
- **Ollama Image**: https://hub.docker.com/r/ollama/ollama
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/docker/

## 🆘 Quick Reference

```bash
# Essential commands
docker-compose up -d              # Start
docker-compose down               # Stop
docker-compose logs -f app        # Logs
docker-compose restart app        # Restart
docker-compose exec app sh        # Shell access

# Database
docker-compose exec mysql mysql -u root -p

# Cleanup
docker-compose down -v            # Remove volumes
docker system prune -a            # Clean everything

# Backup
docker-compose exec -T mysql mysqldump -u root -p${PASSWORD} blog_db > backup.sql
```

---

**For detailed architecture and HITL workflow documentation, see [PROJECT.md](PROJECT.md)**

**For application usage and API docs, see [README.md](README.md)**