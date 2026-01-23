# AI Blog Generator with Human-in-the-Loop

[![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0.5-4285F4.svg?style=flat)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat&logo=Docker&logoColor=white)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A production-ready AI blog generation system with Human-in-the-Loop approval workflow, powered by LangGraph checkpointing and multi-agent orchestration.

## 🌟 Key Features

### 🤖 **Multi-Agent Architecture**
- **Research Agent**: Analyzes topics and creates structured outlines
- **Title Agent**: Generates SEO-friendly, engaging headlines
- **Writer Agent**: Produces comprehensive, well-structured content
- **Editor Agent**: Refines and polishes for publication quality

### ⏸️ **Human-in-the-Loop Workflow**
- **Intelligent Checkpointing**: Workflow pauses at human approval stage using SQLite persistence
- **State Resumption**: Seamlessly continues after human decision
- **Dual Database Architecture**: Separate workflow state (SQLite) and business data (MySQL)
- **Thread-Based Isolation**: Multiple concurrent workflows without interference
- **Approval Management**: Track approvals, rejections, and reasons with timestamps

### 📊 **Real-Time Dashboard**
- Live statistics (Total, Pending, Approved, Rejected)
- Status-based filtering (All, Pending, Approved, Rejected)
- Instant approval/rejection workflow
- Responsive, modern UI

### 🐳 **Docker Ready**
- Complete containerization with Docker Compose
- MySQL, Ollama, and application services orchestrated
- Health checks and automatic restart policies
- Production-ready configuration

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
  - [Docker Deployment](#option-1-docker-recommended)
  - [Local Development](#option-2-local-development)
- [How It Works](#-how-it-works)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Database Schemas](#-database-schemas)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [Production Deployment](#-production-deployment)

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (HTML/CSS/JS)                │
│  • Blog Generation Interface  • Approval Dashboard       │
│  • Real-time Statistics       • Status Filtering         │
└────────────────────┬─────────────────────────────────────┘
                     │ REST API
                     ↓
┌──────────────────────────────────────────────────────────┐
│              FastAPI Backend (main.py)                   │
│  • Blog Generation Endpoints  • Approval Workflow        │
│  • Background Tasks           • State Management         │
└─────────┬────────────────────────┬───────────────────────┘
          │                        │
          ↓                        ↓
┌─────────────────────┐   ┌─────────────────────────────┐
│  MySQL (blog_db)    │   │  LangGraph Workflow         │
│                     │   │  (blog_agents.py)           │
│  • Blog Posts       │   │                             │
│  • Approval Status  │   │  ┌───────────────────────┐  │
│  • Timestamps       │   │  │ Research → Title →    │  │
│  • Rejection Reasons│   │  │ Writer → Editor →     │  │
└─────────────────────┘   │  │ [CHECKPOINT] →        │  │
                          │  │ Human Approval →      │  │
                          │  │ Finalize              │  │
                          │  └───────────────────────┘  │
                          │           ↕                 │
                          │  ┌───────────────────────┐  │
                          │  │ SQLite Checkpointer   │  │
                          │  │ (blog_workflow.db)    │  │
                          │  │ • Workflow States     │  │
                          │  │ • Thread Isolation    │  │
                          │  └───────────────────────┘  │
                          │           ↕                 │
                          │  ┌───────────────────────┐  │
                          │  │ Ollama LLM            │  │
                          │  │ (qwen2.5:0.5b)        │  │
                          │  └───────────────────────┘  │
                          └─────────────────────────────┘
```

### Thread-Based State Management

```
┌─────────────────────────────────────────────────────────┐
│  Blog Generation Request                                │
│  ↓                                                      │
│  Generate unique thread_id: "blog_abc123"               │
│  ↓                                                      │
│  ┌───────────────┐          ┌──────────────────┐        │
│  │ MySQL Record  │←────────→│ SQLite Checkpoint│        │
│  │ id: 1         │ thread_id│ thread_id:       │        │
│  │ thread_id:    │          │ "blog_abc123"    │        │
│  │ "blog_abc123" │          │ state: {...}     │        │
│  │ status: PEND. │          │ next: ["human_   │        │
│  └───────────────┘          │       approval"] │        │
│                             └──────────────────┘        │
│                                                         │
│  Human Decision → Update SQLite → Resume Workflow       │
│                                                         │
│  ┌───────────────┐          ┌──────────────────┐        │
│  │ MySQL Record  │          │ SQLite Checkpoint│        │
│  │ status: APPROV│          │ state: updated   │        │
│  │ approved_at:  │          │ next: []         │        │
│  │ timestamp     │          │ (completed)      │        │
│  └───────────────┘          └──────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (for containerized deployment)
- **OR** Python 3.8+, MySQL, and Ollama (for local development)

### Option 1: Docker (Recommended)

The fastest way to get started with everything pre-configured:

```bash
# Clone the repository
git clone https://github.com/VikasPrajapati1998/BlogGeneration.git
cd BlogGeneration

# Create .env file (copy from .env.example or create new)
cat > .env << EOF
# Database
DATABASE=blog_db
PASSWORD=''
MYSQL_ROOT_PASSWORD=''

# LangChain (optional - for tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key_here
LANGCHAIN_PROJECT=BlogGeneration

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
EOF

# Start all services
docker-compose up -d

# Wait for Ollama model download (first time only)
docker-compose logs -f ollama-pull

# Access application
# Open browser: http://localhost:8000
```

**What happens:**
1. MySQL database starts on port 3307
2. Ollama server starts and downloads `qwen2.5:0.5b` model (~500MB)
3. FastAPI application starts on port 8000
4. All services health-checked and connected

**Manage services:**
```bash
# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build -d

# View service status
docker-compose ps
```

### Option 2: Local Development

For development with hot reload:

```bash
# 1. Install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Setup MySQL
mysql -u root -p
CREATE DATABASE blog_db;
# OR run: python setup_database.py

# 3. Install and start Ollama
# Download from: https://ollama.ai
ollama serve
ollama pull qwen2.5:0.5b

# 4. Configure environment
# Create .env file with your MySQL credentials

# 5. Run application
python main.py

# Access: http://localhost:8000
```

## 🎯 How It Works

### The HITL Workflow

Our system implements a **three-phase Human-in-the-Loop pattern**:

#### **Phase 1: Generation (Before Human)**

```
User submits topic → LangGraph workflow starts
     ↓
Research Agent → Creates outline
     ↓
Title Agent → Generates title
     ↓
Writer Agent → Writes content
     ↓
Editor Agent → Refines content
     ↓
[CHECKPOINT] → Workflow PAUSES
     ↓
State saved to SQLite (blog_workflow.db)
Blog saved to MySQL with status=PENDING
```

**Console Output:**
```
[GENERATE] Starting blog generation (STEP 1: Before Human)
[AGENT] Research Agent: Creating outline...
[AGENT] Title Agent: Generating title...
[AGENT] Writer Agent: Writing blog...
[AGENT] Editor Agent: Refining content...
[GENERATE] ✓ Workflow paused at checkpoint
[GENERATE] Waiting for human decision...
```

#### **Phase 2: Human Decision**

Human reviewer examines the generated content and makes a decision:
- **Approve**: Content is ready for publication
- **Reject**: Content needs improvement (with reason)

#### **Phase 3: Resumption (After Human)**

```
Human decision → Update SQLite checkpoint
     ↓
workflow.update_state(as_node="human_approval")
     ↓
Workflow resumes from checkpoint
     ↓
Router checks approval_status
     ↓
If approved → finalize_approved node
If rejected → handle_rejection node
     ↓
Final status saved to MySQL
Workflow completes
```

**Console Output:**
```
[UPDATE] Human decision received
[UPDATE] Calling update_state(as_node='human_approval')...
[RESUME] Resuming workflow execution
[ROUTER] Routing to APPROVED path
[FINAL] ✓ Blog APPROVED
[RESUME] ✓ Workflow completed
```

### Why Dual Databases?

**SQLite (blog_workflow.db):**
- Manages LangGraph workflow state
- Stores checkpoints for pause/resume
- Handles thread-based isolation
- Persists across server restarts
- Auto-managed by LangGraph

**MySQL (blog_db):**
- Stores final blog posts
- Tracks approval status and timestamps
- Manages rejection reasons
- Optimized for queries and filtering
- User-facing data

**The Bridge:** `thread_id` links both databases, enabling workflow resumption after human decisions.

## 📚 API Documentation

### Blog Generation

**Create Blog (Initiates HITL Workflow)**
```http
POST /api/generate
Content-Type: application/json

{
  "topic": "Future of Artificial Intelligence"
}

Response:
{
  "id": 1,
  "thread_id": "blog_abc123",
  "topic": "Future of Artificial Intelligence",
  "title": "Generating...",
  "content": "Blog generation in progress...",
  "status": "pending",
  "created_at": "2026-01-23T10:30:00",
  "approved_at": null,
  "rejection_reason": null
}
```

### Blog Retrieval

```http
# Get all blogs
GET /api/blogs

# Filter by status
GET /api/blogs?status=pending
GET /api/blogs?status=approved
GET /api/blogs?status=rejected

# Get specific blog
GET /api/blogs/{id}

# Get workflow state
GET /api/blogs/{id}/state
Response:
{
  "approval_status": "pending",
  "next_nodes": ["human_approval"],
  "thread_id": "blog_abc123",
  ...
}
```

### Blog Review (HITL Decision)

**Approve Blog**
```http
POST /api/blogs/{id}/review
Content-Type: application/json

{
  "action": "approve"
}

Response:
{
  "id": 1,
  "status": "approved",
  "approved_at": "2026-01-23T11:45:00",
  ...
}
```

**Reject Blog**
```http
POST /api/blogs/{id}/review
Content-Type: application/json

{
  "action": "reject",
  "rejection_reason": "Needs more specific examples and data"
}

Response:
{
  "id": 1,
  "status": "rejected",
  "rejection_reason": "Needs more specific examples and data",
  ...
}
```

### Statistics

```http
GET /api/stats

Response:
{
  "total": 15,
  "pending": 3,
  "approved": 10,
  "rejected": 2
}
```

### Health Check

```http
GET /health

Response:
{
  "status": "healthy",
  "langchain_project": "BlogGeneration",
  "database": "blog_db"
}
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE=blog_db
PASSWORD=your_secure_password
MYSQL_ROOT_PASSWORD=your_secure_password
DB_HOST=localhost  # Use "mysql" for Docker
DB_PORT=3306       # Use "3307" if running MySQL in Docker
DB_USER=root

# LangChain Configuration (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=BlogGeneration

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434  # http://ollama:11434 in Docker

# Application Configuration
DEBUG=false
MAX_CONCURRENT_GENERATIONS=5
```

### Change LLM Model

Edit `blog_agents.py`:

```python
llm = ChatOllama(
    model="qwen2.5:0.5b",  # Options: llama3.2:1b, mistral:latest, etc.
    temperature=0.7,
    base_url=OLLAMA_BASE_URL,
)
```

**Model Comparison:**

|      Model     |        Speed        |        Quality         |    Size    |    Recommended For    |
|----------------|---------------------|------------------------|------------|-----------------------|
| qwen2.5:0.5b   | ⚡⚡⚡ Fast (18s) | ⭐⭐⭐ Good           |  500MB     | Development, Testing  |
| llama3.2:1b    | ⚡⚡ Medium (33s)  | ⭐⭐⭐⭐ Great       |  1GB       | Balanced Use          |
| mistral:latest | ⚡ Slow (53s)      | ⭐⭐⭐⭐⭐ Excellent |  4GB       | Production            |

## 🗄️ Database Schemas

### MySQL: `blog_posts`

```sql
CREATE TABLE blog_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    thread_id VARCHAR(255) UNIQUE NOT NULL,
    topic VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved_at DATETIME NULL,
    rejection_reason TEXT NULL,
    
    INDEX idx_thread_id (thread_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

### SQLite: `checkpoints` (Auto-managed by LangGraph)

```
Stores:
- thread_id (links to MySQL)
- workflow state (topic, title, content, etc.)
- next_nodes (current position in workflow)
- checkpoint metadata

Inspect with:
sqlite3 blog_workflow.db
SELECT thread_id, checkpoint_ns FROM checkpoints;
```

## 🔧 Troubleshooting

### Docker Issues

**Services not starting:**
```bash
# Check logs
docker-compose logs

# Restart specific service
docker-compose restart app

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

**Port conflicts:**
```bash
# Check what's using ports
netstat -ano | findstr :8000    # Windows
lsof -i :8000                   # Mac/Linux

# Change ports in docker-compose.yml if needed
```

**Ollama model not loading:**
```bash
# Check Ollama container
docker-compose logs ollama

# Manually pull model
docker-compose exec ollama ollama pull qwen2.5:0.5b

# Verify model exists
docker-compose exec ollama ollama list
```

### Workflow Issues

**Workflow not pausing:**
```python
# Verify in blog_agents.py:
compiled = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_approval"]  # Must be present
)

# Check console for:
[GENERATE] ✓ Workflow paused at checkpoint
```

**Workflow not resuming:**
```bash
# Check thread_id consistency
# MySQL:
SELECT id, thread_id, status FROM blog_posts;

# SQLite:
sqlite3 blog_workflow.db
SELECT thread_id FROM checkpoints;

# Thread IDs must match!
```

**State update fails:**
```
Verify:
1. Correct thread_id used
2. as_node="human_approval" specified
3. approval_status value is "approved" or "rejected"
4. Checkpoint exists in SQLite
```

### Database Connection

**MySQL connection failed:**
```bash
# Test connection
mysql -u root -p -h localhost -P 3307

# For Docker:
docker-compose exec mysql mysql -u root -p

# Check credentials in .env match docker-compose.yml
```

**SQLite locked:**
```python
# Ensure check_same_thread=False in blog_agents.py:
conn = sqlite3.connect(
    "blog_workflow.db",
    check_same_thread=False  # Critical for multi-process
)
```

## 💻 Development

### Project Structure

```
BlogGeneration/
├── main.py                 # FastAPI application
├── blog_agents.py          # LangGraph HITL workflow
├── database.py             # MySQL models & connection
├── setup_database.py       # Database initialization
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Application container
├── .env                    # Environment configuration
├── .dockerignore           # Docker build exclusions
├── init.sql                # MySQL initialization
├── blog_workflow.db        # SQLite checkpoints (auto-created)
├── static/
│   ├── index.html         # Frontend UI
│   ├── style.css          # Styling
│   └── script.js          # Client-side logic
└── docs/
    ├── PROJECT.md         # Detailed architecture docs
    ├── DOCKER_README.md   # Docker setup guide
    └── README.md          # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
black *.py

# Lint code
flake8 *.py

# Type checking
mypy *.py
```

## 🚀 Production Deployment

### Environment Configuration

```env
# Production .env
DEBUG=false
MAX_CONCURRENT_GENERATIONS=10

# Use strong passwords
PASSWORD=<strong_random_password>
MYSQL_ROOT_PASSWORD=<strong_random_password>

# Configure allowed origins
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Using Gunicorn

```bash
# Install
pip install gunicorn

# Run with workers
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile access.log \
  --error-logfile error.log
```

### Docker Production

```bash
# Build production image
docker-compose -f docker-compose.yml build

# Run with resource limits
docker-compose up -d

# Monitor
docker stats blog_app blog_mysql blog_ollama
```

### Monitoring

```bash
# Application logs
docker-compose logs -f app

# Database logs
docker-compose logs -f mysql

# Resource usage
docker stats
```

### Backup Strategy

```bash
# Backup MySQL
docker-compose exec -T mysql mysqldump -u root -p${PASSWORD} blog_db > backup_$(date +%Y%m%d).sql

# Backup SQLite checkpoints
cp blog_workflow.db backup_workflow_$(date +%Y%m%d).db

# Restore
cat backup.sql | docker-compose exec -T mysql mysql -u root -p${PASSWORD} blog_db
```

## 📖 Additional Resources

- **Detailed Architecture**: See [PROJECT.md](docs/PROJECT.md)
- **Docker Guide**: See [DOCKER_README.md](docs/DOCKER_README.md)
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Ollama Models**: https://ollama.ai/library

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain Team** for the excellent LangGraph framework
- **FastAPI** for the modern, fast web framework
- **Ollama** for local LLM deployment
- **Community Contributors** for valuable feedback

## 📞 Support

For issues, questions, or feature requests:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review [PROJECT.md](docs/PROJECT.md) for detailed architecture
3. Search existing [GitHub Issues](https://github.com/your-repo/issues)
4. Open a new issue with detailed information

---

**Built with ❤️ using LangChain, LangGraph, FastAPI, and Docker**

**Powered by Vikas Prajapati for production-ready AI workflows**
