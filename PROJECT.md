# AI Blog Generator - Technical Documentation

> Production-grade HITL workflow system with LangGraph checkpointing and containerized deployment

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Browser)                       │
│  HTML5 • CSS3 • Vanilla JavaScript • REST API Client        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python 3.11)                  │
│  • Async Endpoints  • Background Tasks  • CORS Middleware   │
└──────┬──────────────────────────────────────┬───────────────┘
       │                                      │
       ↓                                      ↓
┌──────────────────┐              ┌─────────────────────────┐
│  MySQL (blog_db) │              │  LangGraph Workflow     │
│                  │              │                         │
│  blog_posts:     │              │  ┌──────────────────┐   │
│  • id            │◄─────────────┤  │ Multi-Agent Flow │   │
│  • thread_id ────┼──────────┐   │  │                  │   │
│  • topic         │          │   │  │ Research         │   │
│  • title         │          │   │  │    ↓             │   │
│  • content       │          │   │  │ Title            │   │
│  • status        │          │   │  │    ↓             │   │
│  • approved_at   │          │   │  │ Writer           │   │
│  • rejection_    │          │   │  │    ↓             │   │
│    reason        │          │   │  │ Editor           │   │
└──────────────────┘          │   │  │    ↓             │   │
                              │   │  │ [CHECKPOINT]     │   │
                              │   │  │    ↓             │   │
                              │   │  │ Human Approval   │   │
                              │   │  │    ↓             │   │
                              │   │  │ Finalize/Reject  │   │
                              │   │  └──────────────────┘   │
                              │   │           ↕             │
                              │   │  ┌──────────────────┐   │
                              └───┼──┤ SQLite Checkpoint│   │
                                  │  │ (blog_workflow.db)│  │
                                  │  │ • thread_id      │   │
                                  │  │ • state data     │   │
                                  │  │ • next_nodes     │   │
                                  │  └──────────────────┘   │
                                  │           ↕             │
                                  │  ┌──────────────────┐   │
                                  │  │ Ollama LLM       │   │
                                  │  │ qwen2.5:0.5b     │   │
                                  │  └──────────────────┘   │
                                  └─────────────────────────┘
```

### Docker Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Docker Compose Network (bloggeneration_blog_network)   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌───────────┐    │
│  │   MySQL      │   │   Ollama     │   │   App     │    │
│  │              │   │              │   │           │    │
│  │ blog_mysql   │   │ blog_ollama  │   │ blog_app  │    │
│  │ Port: 3307   │   │ Port: 11434  │   │ Port:8000 │    │
│  │ Image:       │   │ Image:       │   │ Build:    │    │
│  │ mysql:8.0    │   │ ollama:latest│   │ Dockerfile│    │
│  │              │   │              │   │           │    │
│  │ Volume:      │   │ Volume:      │   │ Volume:   │    │
│  │ mysql_data   │   │ ollama_data  │   │ checkpoint│    │
│  │ init.sql (ro)│   │ (~500MB)     │   │ _data     │    │
│  └──────┬───────┘   └──────┬───────┘   └─────┬─────┘    │
│         │                  │                 │          │
│         └──────────────────┴─────────────────┘          │
│                            │                            │
│                  ┌─────────┴────────┐                   │
│                  │  ollama-pull     │                   │
│                  │  (init service)  │                   │
│                  │  Runs once       │                   │
│                  └──────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## 🔄 HITL Workflow Pattern

### Three-Phase Execution Model

```
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: GENERATION (Automated)                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  POST /api/generate                                     │
│    ↓                                                    │
│  Generate thread_id: "blog_abc123"                      │
│    ↓                                                    │
│  Create MySQL record (status=PENDING)                   │
│    ↓                                                    │
│  Background Task: generate_blog_async()                 │
│    ├─→ Research Agent  → state.outline                  │
│    ├─→ Title Agent     → state.title                    │
│    ├─→ Writer Agent    → state.content                  │
│    └─→ Editor Agent    → state.refined_content          │
│    ↓                                                    │
│  interrupt_before=["human_approval"]                    │
│    ↓                                                    │
│  Save checkpoint to SQLite                              │
│    ├─→ thread_id: "blog_abc123"                         │
│    ├─→ values: {topic, title, content, ...}             │
│    └─→ next: ["human_approval"]                         │
│    ↓                                                    │
│  Update MySQL (title, content, status=PENDING)          │
│    ↓                                                    │
│  WORKFLOW PAUSED                                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: HUMAN DECISION (Manual)                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Human reviews content → Decision                       │
│    ↓                                                    │
│  POST /api/blogs/{id}/review                            │
│    {action: "approve"} OR {action: "reject", reason}    │
│    ↓                                                    │
│  Backend: update_approval_status(thread_id, action)     │
│    ├─→ Load checkpoint from SQLite                      │
│    ├─→ workflow.get_state(config)                       │
│    ├─→ Prepare new_values {approval_status: "approved"} │
│    └─→ workflow.update_state(                           │
│           config,                                       │
│           new_values,                                   │
│           as_node="human_approval"  ← Critical          │
│        )                                                │
│    ↓                                                    │
│  Checkpoint updated in SQLite                           │
│    └─→ next: ["finalize_approved"] or ["handle_reject"] │
│                                                         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 3: RESUMPTION (Automated)                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  workflow.invoke(None, config)  ← Resume from checkpoint│
│    ↓                                                    │
│  Load checkpoint from SQLite                            │
│    ↓                                                    │
│  Router: route_approval(state)                          │
│    ├─→ if approved → "finalize_approved"                │
│    └─→ if rejected → "handle_rejection"                 │
│    ↓                                                    │
│  Execute final node                                     │
│    ↓                                                    │
│  Update MySQL                                           │
│    ├─→ status = APPROVED/REJECTED                       │
│    ├─→ approved_at = NOW() (if approved)                │
│    └─→ rejection_reason (if rejected)                   │
│    ↓                                                    │
│  WORKFLOW COMPLETE (next: [])                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Critical Implementation Details

**1. Workflow Compilation (blog_agents.py)**

```python
def create_blog_workflow():
    checkpointer = SqliteSaver(
        sqlite3.connect("blog_workflow.db", check_same_thread=False)
    )
    
    workflow = StateGraph(BlogState)
    # Add nodes: research → title → writer → editor → human_approval
    
    compiled = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_approval"]  # Pause point
    )
    return compiled
```

**2. State Update Pattern (HITL Core)**

```python
def update_approval_status(thread_id, action, rejection_reason=None):
    workflow = get_workflow()
    config = {"configurable": {"thread_id": thread_id}}
    
    # Prepare update
    new_values = {"approval_status": action}
    if action == "reject":
        new_values["rejection_reason"] = rejection_reason
    
    # Update as if human_approval node executed
    workflow.update_state(config, new_values, as_node="human_approval")
    
    # Resume from checkpoint
    result = workflow.invoke(None, config)
    return result
```

**3. Background Task Pattern (main.py)**

```python
@app.post("/api/generate")
async def create_blog(request, background_tasks, db):
    thread_id = f"blog_{uuid.uuid4().hex[:16]}"
    
    # Create placeholder record
    blog_post = BlogPost(thread_id=thread_id, status=PENDING)
    db.add(blog_post)
    db.commit()
    
    # Start async generation
    background_tasks.add_task(generate_blog_async, topic, thread_id, blog_post.id)
    
    return BlogResponse(...)  # Return immediately
```

## 🗄️ Dual Database Strategy

### Separation of Concerns

| Aspect | SQLite (blog_workflow.db) | MySQL (blog_db) |
|--------|--------------------------|-----------------|
| **Purpose** | Workflow state management | Business data storage |
| **Managed By** | LangGraph (auto) | SQLAlchemy ORM |
| **Contains** | Checkpoints, thread state | Blog posts, metadata |
| **Schema** | Internal LangGraph | User-defined |
| **Queries** | Via workflow API | Direct SQL/ORM |
| **Persistence** | Across restarts | Permanent storage |
| **Scaling** | Single-instance | Can be replicated |

### Thread ID Linkage

```python
# Generation
thread_id = "blog_abc123"

# SQLite Checkpoint
checkpoints.thread_id = "blog_abc123"
checkpoints.checkpoint = {state data...}

# MySQL Record
blog_posts.thread_id = "blog_abc123"
blog_posts.status = "pending"

# Linkage enables:
# 1. Find checkpoint for blog: SELECT * FROM checkpoints WHERE thread_id = ?
# 2. Find blog for checkpoint: SELECT * FROM blog_posts WHERE thread_id = ?
# 3. Resume workflow after human decision
```

## 📊 Database Schemas

### MySQL: blog_posts

```sql
CREATE TABLE blog_posts (
    id                INT PRIMARY KEY AUTO_INCREMENT,
    thread_id         VARCHAR(255) UNIQUE NOT NULL,  -- Links to SQLite
    topic             VARCHAR(255) NOT NULL,
    title             VARCHAR(500) NOT NULL,
    content           TEXT NOT NULL,
    status            ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved_at       DATETIME NULL,
    rejection_reason  TEXT NULL,
    
    INDEX idx_thread_id (thread_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

### SQLite: checkpoints (Auto-managed by LangGraph)

```sql
-- Simplified representation (actual schema is internal)
checkpoints (
    thread_id          TEXT PRIMARY KEY,
    checkpoint_ns      TEXT,
    checkpoint_id      TEXT,
    checkpoint         BLOB,  -- Serialized state
    metadata           BLOB
)
```

## 🔌 API Endpoints

### Blog Generation

```http
POST /api/generate
Body: {"topic": "AI Technology"}
Response: {id, thread_id, status: "pending", ...}

# Triggers Phase 1, returns immediately
# Background: Agents execute → Checkpoint created → Workflow paused
```

### Blog Retrieval

```http
GET /api/blogs?status=pending
GET /api/blogs/{id}
GET /api/blogs/{id}/state  # Returns workflow state from SQLite
```

### Blog Review (HITL Decision)

```http
POST /api/blogs/{id}/review
Body: {"action": "approve"}
Body: {"action": "reject", "rejection_reason": "..."}

# Triggers Phase 2 + 3:
# - Updates SQLite checkpoint
# - Resumes workflow
# - Completes with final status in MySQL
```

### Statistics

```http
GET /api/stats
Response: {total, pending, approved, rejected}

GET /health
Response: {status: "healthy", ...}
```

## 🐳 Docker Implementation

### Service Configuration

**docker-compose.yml:**

```yaml
services:
  mysql:
    image: mysql:8.0
    ports: ["3307:3306"]
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    environment:
      MYSQL_ROOT_PASSWORD: ${PASSWORD}
      MYSQL_DATABASE: blog_db
    healthcheck:
      test: mysqladmin ping -h localhost

  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes:
      - ollama_data:/root/.ollama
    healthcheck:
      test: ollama list

  app:
    build: .
    ports: ["8000:8000"]
    depends_on:
      mysql: {condition: service_healthy}
      ollama: {condition: service_healthy}
    volumes:
      - checkpoint_data:/app/data  # SQLite persistence
    environment:
      DB_HOST: mysql                # Container name
      OLLAMA_BASE_URL: http://ollama:11434
    healthcheck:
      test: curl -f http://localhost:8000/health

volumes:
  mysql_data:
  ollama_data:
  checkpoint_data:
```

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy application
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Volume Strategy

| Volume | Purpose | Size | Persistence |
|--------|---------|------|-------------|
| `mysql_data` | MySQL database files | ~100MB | Critical |
| `ollama_data` | LLM model storage | ~500MB-4GB | Critical |
| `checkpoint_data` | SQLite workflow state | ~1MB/100 checkpoints | Critical |

## 🔍 State Management Flow

### Checkpoint Lifecycle

```
1. CREATION (Phase 1)
   workflow.invoke(initial_state, config)
   → Agents execute sequentially
   → interrupt_before triggers at human_approval
   → State saved to SQLite
   
2. PAUSE
   Workflow execution halts
   State persists in blog_workflow.db
   MySQL shows status=PENDING
   
3. UPDATE (Phase 2)
   workflow.update_state(config, values, as_node="human_approval")
   → Checkpoint updated in SQLite
   → next_nodes modified based on decision
   
4. RESUMPTION (Phase 3)
   workflow.invoke(None, config)  # None = continue from checkpoint
   → State loaded from SQLite
   → Execution continues from next_nodes
   → Final node executes
   
5. COMPLETION
   Workflow ends (next = [])
   MySQL updated with final status
   SQLite checkpoint remains for audit
```

### Thread Isolation

```python
# Multiple concurrent workflows
thread_1 = "blog_abc123"  # At editor stage
thread_2 = "blog_def456"  # At human_approval (paused)
thread_3 = "blog_ghi789"  # Completed

# Each has independent:
# - SQLite checkpoint
# - MySQL record
# - Workflow state
# - No interference between threads
```

## 📈 Performance Characteristics

### Timing Benchmarks (qwen2.5:0.5b)

| Operation | Time | Notes |
|-----------|------|-------|
| Research Agent | 3s | Outline generation |
| Title Agent | 2s | Title creation |
| Writer Agent | 8s | Content writing |
| Editor Agent | 5s | Refinement |
| **Total Generation** | **18s** | Until checkpoint |
| Checkpoint Save | <100ms | SQLite write |
| State Load | <50ms | SQLite read |
| State Update | <50ms | SQLite update |
| Workflow Resume | <100ms | Execution continuation |

### Resource Usage

```
Memory (per workflow):
  - Agent execution: ~100-200MB
  - Checkpoint data: ~10-50KB
  - Model loading: ~500MB (shared)

Storage:
  - SQLite: ~1MB/100 checkpoints
  - MySQL: ~1KB/blog post

CPU:
  - Generation: 20-60s (model dependent)
  - Checkpoint ops: <100ms
```

## 🔐 Security Considerations

### Environment Isolation

```bash
# .env file (never commit)
DATABASE=blog_db
PASSWORD=strong_random_password
MYSQL_ROOT_PASSWORD=strong_random_password

# Docker secrets (production)
docker secret create db_password password.txt
```

### Network Security

```yaml
# Docker internal network
networks:
  blog_network:
    driver: bridge
    internal: false  # Set true for complete isolation
```

### Input Validation

```python
class BlogRequest(BaseModel):
    topic: str
    
    @validator('topic')
    def validate_topic(cls, v):
        if not 3 <= len(v) <= 500:
            raise ValueError("Topic length must be 3-500 chars")
        return v
```

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/test_agents.py
def test_workflow_pauses_at_checkpoint():
    workflow = create_blog_workflow()
    result = workflow.invoke(initial_state, config)
    state = workflow.get_state(config)
    assert state.next == ("human_approval",)
```

### Integration Tests

```python
# tests/test_api.py
def test_approve_blog_workflow():
    # Generate
    response = client.post("/api/generate", json={"topic": "Test"})
    blog_id = response.json()["id"]
    
    # Wait for generation
    time.sleep(30)
    
    # Approve
    response = client.post(f"/api/blogs/{blog_id}/review", 
                          json={"action": "approve"})
    assert response.json()["status"] == "approved"
```

## 🚀 Deployment

### Production Checklist

```bash
# 1. Environment
cp .env.example .env
# Edit with production credentials

# 2. Build
docker-compose build --no-cache

# 3. Deploy
docker-compose up -d

# 4. Verify
docker-compose ps
curl http://localhost:8000/health

# 5. Monitor
docker-compose logs -f app
```

### Monitoring

```bash
# Logs
docker-compose logs -f app

# Metrics
docker stats blog_app blog_mysql blog_ollama

# Health
watch -n 5 'curl -s http://localhost:8000/health | jq'
```

### Backup

```bash
# MySQL
docker-compose exec -T mysql mysqldump -u root -p${PASSWORD} blog_db > backup.sql

# SQLite checkpoints
docker cp blog_app:/app/data/blog_workflow.db ./backup_workflow.db

# Volumes
docker run --rm -v bloggeneration_checkpoint_data:/data \
  -v $(pwd)/backups:/backup alpine \
  tar czf /backup/checkpoint_$(date +%Y%m%d).tar.gz -C /data .
```

## 📚 Key Takeaways

### HITL Pattern Benefits

1. **State Persistence**: Workflows survive server restarts
2. **Thread Isolation**: Multiple concurrent workflows
3. **Clean Separation**: Workflow state vs. business data
4. **Resume Capability**: Continue from any checkpoint
5. **Audit Trail**: Full state history in SQLite

### Docker Benefits

1. **Reproducibility**: Identical environment across machines
2. **Isolation**: Services in separate containers
3. **Scalability**: Easy horizontal scaling
4. **Portability**: Works on any Docker-supported OS
5. **Version Control**: Infrastructure as code

### Production Considerations

1. **Use PostgreSQL** checkpointer for distributed deployments
2. **Implement rate limiting** on generation endpoints
3. **Add authentication** for multi-user scenarios
4. **Monitor checkpoint size** for cleanup automation
5. **Set up alerting** for workflow failures

---

**For detailed API documentation, see [README.md](README.md)**

**For Docker operations guide, see [DOCKER_README.md](DOCKER_README.md)**
