# Docker Setup for Windows - AI Blog Generator

## Prerequisites for Windows

### 1. Install Docker Desktop for Windows

Download and install from: https://www.docker.com/products/docker-desktop/

**System Requirements:**
- Windows 10/11 Pro, Enterprise, or Education (64-bit)
- OR Windows 10/11 Home with WSL 2
- Hyper-V and Containers Windows features enabled
- At least 8GB RAM

**Installation Steps:**
1. Download Docker Desktop installer
2. Run installer as Administrator
3. Enable WSL 2 during installation (recommended)
4. Restart computer when prompted
5. Start Docker Desktop
6. Verify installation:
   ```powershell
   docker --version
   docker-compose --version
   ```

### 2. Verify Your Current Setup

Based on your directory listing, you have:
```
✓ Python 3.11.9 in venv
✓ All project files present
✓ blog_workflow.db already created (626KB)
✓ Static files present
```

## Quick Start on Windows

### Step 1: Open PowerShell or Command Prompt

```powershell
# Navigate to your project directory
cd "D:\Study\Projects\Blog Generation\BlogGeneration"
```

### Step 2: Create Required Docker Files

Copy the following files to your project directory:
- `Dockerfile` (already provided)
- `docker-compose.yml` (already provided)
- `.dockerignore` (already provided)
- `init.sql` (already provided)

### Step 3: Update .env File for Docker

Your current `.env` should work, but make sure it has:

```env
# Database Configuration
DATABASE=blog_db
PASSWORD=abcd@1234

# LangChain Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_api_key_here
LANGCHAIN_PROJECT=BlogGeneration

# Application Configuration
DEBUG=false
MAX_CONCURRENT_GENERATIONS=5

# Get Ollama URL from environment variable (set in docker-compose.yml)
OLLAMA_BASE_URL = "http://localhost:11434"
```

### Step 4: Build and Run with Docker Compose

```powershell
# Docker Images
docker images
docker ps -a

# Remove images (if rebuilding after changes)
docker rmi -f 415961b5186e

# Remove dangling images (optional but recommended after project changes)
docker builder prune
docker builder prune -a
docker system prune -f

# Build all services (use --no-cache if you've changed dependencies)
docker-compose build -d
docker-compose build --no-cache app

# Rebuild and restart everything (useful after code changes)
docker-compose up --build -d
docker-compose up --build -d app
docker-compose build --no-cache app

# Start all services
docker compose up
docker-compose up -d
docker-compose up -d app

# Check status
docker-compose ps

# Check logs (monitor AI generation logs)
docker-compose logs -f app

# Pull Ollama model (qwen2.5:0.5b for Gen AI)
docker-compose up ollama-pull

# Check if model is downloaded
docker-compose exec ollama ollama list
```

### Step 5: Wait for Ollama Model Download

The first run will download the Ollama model (~400MB):

```powershell
# Monitor the download progress
docker-compose logs -f ollama-pull

# You should see:
# "Pulling qwen2.5:0.5b model..."
# "Model pulled successfully!"
```

### Step 6: Verify Everything is Running

```powershell
# Check all services
docker-compose ps

# Should show all services as "Up (healthy)"

# Test the application
curl http://localhost:8000/health
# Or open in browser: http://localhost:8000/health
```

### Step 7: Access the Application

Open your browser and go to: **http://localhost:8000**

## Windows-Specific Commands

### Using PowerShell

```powershell
# Start services
docker-compose up -d
docker-compose up -d app

# View logs
docker-compose logs -f
docker logs blog_app
docker logs -f blog_app

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Check service status
docker-compose ps

# View resource usage
docker stats blog_app blog_mysql blog_ollama
```

### Using Command Prompt (CMD)

Same commands work in CMD:

```cmd
docker-compose up -d
docker-compose logs -f
docker-compose down
docker-compose ps
```

## Working with Your Existing Database

Since you already have `blog_workflow.db` locally:

### Option 1: Use Docker Volumes (Recommended)

The checkpoint database will be created fresh in Docker:

```powershell
# This is automatic - Docker will create a new blog_workflow.db
docker-compose up -d
```

### Option 2: Mount Your Existing Database

Modify `docker-compose.yml`:

```yaml
app:
  volumes:
    - checkpoint_data:/app/data
    - ./blog_workflow.db:/app/blog_workflow.db
```

Then:
```powershell
docker-compose up -d
```

## Windows Path Considerations

### File Paths in docker-compose.yml

Windows paths should use forward slashes in Docker:

```yaml
# Correct
- ./static:/app/static

# Also works
- D:/Study/Projects/Blog Generation/BlogGeneration/static:/app/static
```

### Volume Mounting

Docker Desktop for Windows handles volume mounting automatically:

```yaml
volumes:
  - ./blog_workflow.db:/app/blog_workflow.db  # Windows path converted automatically
```

## Troubleshooting on Windows

### Issue: Docker Desktop Won't Start

**Solution:**
1. Enable Hyper-V:
   ```powershell
   # Run PowerShell as Administrator
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
   ```

2. Enable WSL 2:
   ```powershell
   # Run PowerShell as Administrator
   wsl --install
   wsl --set-default-version 2
   ```

3. Restart computer

### Issue: Port Already in Use

**Check what's using the port:**
```powershell
# Check port 8000
netstat -ano | findstr :8000

# Check port 3306 (MySQL)
netstat -ano | findstr :3306

# Check port 11434 (Ollama)
netstat -ano | findstr :11434
```

**Kill the process:**
```powershell
# Find PID from netstat output, then:
taskkill /PID <PID> /F

# Example:
taskkill /PID 12345 /F
```

### Issue: Permission Denied Errors

**Solution:**
1. Run PowerShell/CMD as Administrator
2. Or adjust Docker Desktop settings:
   - Docker Desktop → Settings → Resources → File Sharing
   - Add your project directory

### Issue: Slow Performance

**Solution:**
1. Allocate more resources to Docker:
   - Docker Desktop → Settings → Resources
   - Increase CPUs to 4+
   - Increase Memory to 8GB+
   - Increase Disk image size to 50GB+

2. Use WSL 2 backend (faster than Hyper-V):
   - Docker Desktop → Settings → General
   - Enable "Use the WSL 2 based engine"

### Issue: Volume Mounting Not Working

**Solution:**
```powershell
# Reset Docker Desktop
# Docker Desktop → Troubleshoot → Reset to factory defaults

# Or manually reset volumes
docker-compose down -v
docker volume prune -f
docker-compose up -d
```

### Issue: MySQL Connection Failed

**Check MySQL is running:**
```powershell
docker-compose ps mysql

# View MySQL logs
docker-compose logs mysql

# Access MySQL shell
docker-compose exec mysql mysql -u root -p
# Password: abcd@1234 (or your .env PASSWORD)
```

**Test connection:**
```powershell
# From Windows (if MySQL client installed)
mysql -h 127.0.0.1 -P 3306 -u root -p

# Or from Docker
docker-compose exec mysql mysql -u root -p
```

## Combining Local Development with Docker

### Scenario 1: Run Only Database in Docker

Use Docker for MySQL and Ollama, run app locally:

```powershell
# Start only MySQL and Ollama
docker-compose up -d mysql ollama

# Wait for services to be ready
timeout 20

# In your venv, run app locally
venv\Scripts\activate
python main.py
```

Update connection in `database.py`:
```python
DB_HOST = "localhost"  # Instead of "mysql"
```

### Scenario 2: Run Everything in Docker

```powershell
docker-compose up -d
```

### Scenario 3: Development Mode

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  app:
    volumes:
      - .:/app  # Mount entire directory for hot reload
    environment:
      DEBUG: "true"
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Run:
```powershell
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Windows Batch Scripts

Create `start.bat`:

```batch
@echo off
echo Starting AI Blog Generator...
docker-compose up -d
echo.
echo Services starting...
timeout /t 10 /nobreak >nul
docker-compose ps
echo.
echo Application available at: http://localhost:8000
pause
```

Create `stop.bat`:

```batch
@echo off
echo Stopping AI Blog Generator...
docker-compose down
echo.
echo All services stopped.
pause
```

Create `logs.bat`:

```batch
@echo off
docker-compose logs -f
```

Create `restart.bat`:

```batch
@echo off
echo Restarting AI Blog Generator...
docker-compose restart
echo.
echo Services restarted.
docker-compose ps
pause
```

## PowerShell Functions

Add to your PowerShell profile:

```powershell
# Edit profile
notepad $PROFILE

# Add these functions:

function Start-BlogGen {
    Set-Location "D:\Study\Projects\Blog Generation\BlogGeneration"
    docker-compose up -d
    Write-Host "Services starting..." -ForegroundColor Green
    Start-Sleep -Seconds 10
    docker-compose ps
    Write-Host "`nApplication: http://localhost:8000" -ForegroundColor Cyan
}

function Stop-BlogGen {
    Set-Location "D:\Study\Projects\Blog Generation\BlogGeneration"
    docker-compose down
    Write-Host "Services stopped." -ForegroundColor Yellow
}

function Show-BlogGenLogs {
    Set-Location "D:\Study\Projects\Blog Generation\BlogGeneration"
    docker-compose logs -f
}

function Show-BlogGenStatus {
    Set-Location "D:\Study\Projects\Blog Generation\BlogGeneration"
    docker-compose ps
}
```

Then use:
```powershell
Start-BlogGen
Stop-BlogGen
Show-BlogGenLogs
Show-BlogGenStatus
```

## Backup and Restore on Windows

### Backup Everything

```powershell
# Create backups directory
mkdir backups

# Backup MySQL
docker-compose exec -T mysql mysqldump -u root -pabcd@1234 blog_db > backups\blog_db_backup.sql

# Backup volumes
docker run --rm -v blog_generation_checkpoint_data:/data -v ${PWD}/backups:/backup alpine tar czf /backup/checkpoint_backup.tar.gz -C /data .

docker run --rm -v blog_generation_mysql_data:/data -v ${PWD}/backups:/backup alpine tar czf /backup/mysql_backup.tar.gz -C /data .
```

### Restore from Backup

```powershell
# Restore MySQL
Get-Content backups\blog_db_backup.sql | docker-compose exec -T mysql mysql -u root -pabcd@1234 blog_db

# Restore volumes
docker run --rm -v blog_generation_checkpoint_data:/data -v ${PWD}/backups:/backup alpine tar xzf /backup/checkpoint_backup.tar.gz -C /data
```

## Performance Tips for Windows

1. **Enable WSL 2** (much faster):
   - Docker Desktop → Settings → General → Use WSL 2

2. **Store files in WSL 2** (optional, for better performance):
   ```powershell
   # Access WSL filesystem
   wsl
   cd /home/your_username/
   # Clone/move project here
   ```

3. **Increase Docker Resources**:
   - Docker Desktop → Settings → Resources
   - CPUs: 4-6
   - Memory: 8GB+
   - Swap: 2GB
   - Disk: 50GB+

4. **Disable Antivirus Scanning** for Docker directories:
   - Add exclusions for:
     - `C:\ProgramData\Docker`
     - `C:\Users\<YourUser>\AppData\Local\Docker`
     - Your project directory

## Next Steps

1. **Start the stack:**
   ```powershell
   cd "D:\Study\Projects\Blog Generation\BlogGeneration"
   docker-compose up -d
   ```

2. **Monitor logs:**
   ```powershell
   docker-compose logs -f
   ```

3. **Access application:**
   - Open browser: http://localhost:8000

4. **Stop when done:**
   ```powershell
   docker-compose down
   ```

## Additional Resources

- Docker Desktop for Windows: https://docs.docker.com/desktop/windows/
- WSL 2 Setup: https://docs.microsoft.com/en-us/windows/wsl/install
- Docker Compose: https://docs.docker.com/compose/
- Troubleshooting: https://docs.docker.com/desktop/troubleshoot/overview/

---

**Your Windows setup is ready! Just run `docker-compose up -d` to get started!**

