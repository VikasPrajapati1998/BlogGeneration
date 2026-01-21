# AI Blog Generator with Human-in-the-Loop Approval

A complete blog generation application using LangChain, LangGraph, FastAPI, and MySQL with a **Human-in-the-Loop (HITL)** approval workflow powered by SQLite checkpointing.

## Features

- **Multi-Agent Blog Generation**: Uses LangGraph with 4 specialized agents:
  - Research Agent: Creates blog outlines
  - Title Agent: Generates engaging titles
  - Writer Agent: Writes comprehensive content
  - Editor Agent: Refines and polishes the content

- **Human-in-the-Loop (HITL) Workflow**: 
  - **Workflow Interruption**: Generation pauses at human approval checkpoint
  - **SQLite Checkpointing**: Persistent state management across sessions
  - **State Resumption**: Workflow continues after human decision
  - **Dual Database**: SQLite for workflow state, MySQL for blog storage
  - All generated blogs start in "PENDING" status
  - Human reviewers can approve or reject blogs
  - Rejection reasons are tracked and stored
  - Approval timestamps recorded
  - Filter blogs by status (Pending/Approved/Rejected)

- **Real-time Statistics Dashboard**: 
  - Total blogs count
  - Pending approvals
  - Approved blogs
  - Rejected blogs

- **FastAPI Backend**: RESTful API with MySQL database
- **Responsive Frontend**: Clean HTML/CSS/JavaScript interface
- **Full CRUD Operations**: Create, read, update approval status, and delete blog posts

## Project Structure

```
blog_generation/
├── main.py              # FastAPI application with approval endpoints
├── database.py          # MySQL database models with approval status
├── blog_agents.py       # LangGraph HITL workflow and agents
├── setup_database.py    # MySQL database setup script
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── blog_workflow.db     # SQLite checkpoint database (auto-created)
├── static/
│   ├── index.html      # Frontend UI with approval interface
│   ├── style.css       # Styling with status badges
│   └── script.js       # JavaScript logic with review functions
└── README.md           # This file
```

## Prerequisites

1. **Python 3.8+**
2. **MySQL Server** running on localhost
3. **Ollama** with qwen2.5:0.5b model installed

### Install Ollama and Model

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.ai

# Pull the model
ollama pull qwen2.5:0.5b  # Faster, smaller
# OR
ollama pull llama3.2:1b   # Better quality
```

## Setup Instructions

### 1. Clone/Create Project Structure

```bash
mkdir blog_generation
cd blog_generation

# Create static folder
mkdir static

# Copy all files to respective locations:
# - main.py, database.py, blog_agents.py, setup_database.py, .env in root
# - index.html, style.css, script.js in static/
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT='https://api.smith.langchain.com'
LANGCHAIN_API_KEY='your_langchain_api_key_here'
LANGCHAIN_PROJECT='BlogGeneration'

DATABASE=blog_db
USER=localhost
PASSWORD=your_mysql_password_here
```

### 3. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

**Required packages include:**
- `langgraph` - Graph orchestration
- `langgraph-checkpoint-sqlite` - SQLite state persistence for HITL
- `langchain` and `langchain-community` - LLM integration
- `fastapi` and `uvicorn` - Web framework
- `sqlalchemy` and `pymysql` - MySQL ORM
- `python-dotenv` - Environment management

### 4. Setup MySQL Database

```bash
# Run the database setup script
python setup_database.py
```

This will create the `blog_db` database with the necessary tables including approval status fields.

### 5. Run the Application

```bash
# Make sure Ollama is running
ollama serve

# In another terminal, run the FastAPI app
python main.py
```

The application will be available at: **http://localhost:8000**

**Note:** On first run, `blog_workflow.db` (SQLite checkpoint database) will be automatically created for HITL state management.

## Usage

### 1. Generate a Blog

1. Enter a topic in the input field
2. Click "Generate Blog"
3. Wait for the AI agents to create your content (30-60 seconds)
4. **HITL Checkpoint**: Workflow pauses automatically at human approval
5. The generated blog will appear with **PENDING** status
6. Review buttons (Approve/Reject) will be available

### 2. Review and Approve Blogs

**From the Generated Blog View:**
- Click "✓ Approve Blog" to approve
- Click "✗ Reject Blog" to reject (requires reason)

**From the Blog List:**
- Each pending blog has "Approve" and "Reject" buttons
- Click to review directly from the list
- Approved blogs show approval timestamp
- Rejected blogs show rejection reason

**What happens during approval:**
1. Your decision updates the workflow checkpoint in SQLite
2. The workflow resumes from the paused state
3. Routes to approval or rejection handler
4. Final status is saved to MySQL database

### 3. Filter Blogs by Status

Use the filter tabs to view:
- **All**: All blogs regardless of status
- **Pending**: Blogs awaiting approval (paused at HITL checkpoint)
- **Approved**: Approved blogs ready for publishing
- **Rejected**: Rejected blogs with reasons

### 4. Monitor Statistics

The dashboard shows real-time counts:
- Total blogs generated
- Pending approvals (workflows paused at checkpoint)
- Approved blogs
- Rejected blogs

### 5. API Endpoints

**Blog Generation:**
- `POST /api/generate` - Generate new blog (creates with PENDING status, pauses at HITL checkpoint)

**Blog Retrieval:**
- `GET /api/blogs` - Get all blogs
- `GET /api/blogs?status=pending` - Get pending blogs
- `GET /api/blogs?status=approved` - Get approved blogs
- `GET /api/blogs?status=rejected` - Get rejected blogs
- `GET /api/blogs/{id}` - Get specific blog
- `GET /api/blogs/{id}/state` - Get workflow state for a blog

**Blog Review:**
- `POST /api/blogs/{id}/review` - Approve or reject a blog (resumes workflow from checkpoint)
  ```json
  // Approve
  {"action": "approve"}
  
  // Reject
  {"action": "reject", "rejection_reason": "Needs more detail"}
  ```

**Blog Management:**
- `DELETE /api/blogs/{id}` - Delete blog

**Statistics:**
- `GET /api/stats` - Get approval statistics
- `GET /health` - Health check

## How It Works - HITL Pattern

### LangGraph Workflow with HITL

The blog generation follows this workflow with a **Human-in-the-Loop checkpoint**:

```
Research → Title → Writer → Editor → [CHECKPOINT] → Human Review → Approved/Rejected
```

**Phase 1: Generation (Before Human)**
1. **Research Agent**: Analyzes the topic and creates a structured outline
2. **Title Agent**: Generates an SEO-friendly, engaging title
3. **Writer Agent**: Writes comprehensive content based on the outline
4. **Editor Agent**: Reviews and refines the content for clarity and quality
5. **Checkpoint**: Workflow pauses with `interrupt_before=["human_approval"]`
6. **State Saved**: Current state saved to `blog_workflow.db` (SQLite)
7. **Status**: Blog saved to MySQL with PENDING status

**Phase 2: Human Decision**
1. Human reviewer examines the generated content
2. Makes decision: Approve or Reject
3. Frontend calls `/api/blogs/{id}/review` endpoint
4. Backend updates workflow state using `update_state(as_node="human_approval")`

**Phase 3: Workflow Resumption (After Human)**
1. Workflow automatically resumes from checkpoint
2. Routes based on approval_status:
   - If approved → `finalize_approved` node
   - If rejected → `handle_rejection` node
3. Final status saved to MySQL database
4. Workflow completes

### Dual Database Architecture

```
┌─────────────────────────────────────────┐
│         blog_workflow.db (SQLite)       │
│  - Workflow checkpoints                 │
│  - Intermediate states                  │
│  - Thread-based state management        │
│  - Auto-created and managed by LangGraph│
└─────────────────────────────────────────┘
                    │
                    │ State persistence
                    ↓
┌─────────────────────────────────────────┐
│         blog_db (MySQL)                 │
│  - Final blog posts                     │
│  - Approval status                      │
│  - Timestamps                           │
│  - Rejection reasons                    │
└─────────────────────────────────────────┘
```

**Why Two Databases?**
- **SQLite (blog_workflow.db)**: Handles workflow state, checkpoints, and resumption
- **MySQL (blog_db)**: Stores final blog posts and approval metadata
- **Separation of Concerns**: Workflow logic separate from business data
- **Persistence**: Workflow survives server restarts

### Checkpoint Management

Each blog generation creates a unique **thread_id** (e.g., `blog_abc123`):
- Thread ID links SQLite checkpoint to MySQL blog record
- Enables workflow resumption after server restart
- Allows multiple concurrent blog generations
- State isolated per thread

### Agent Communication

Each agent receives the state from the previous agent and adds its contribution:
- State contains: `topic`, `title`, `outline`, `content`, `refined_content`, `approval_status`
- Agents pass the enriched state through the workflow
- State checkpointed at human approval node
- Final output saved to MySQL after human decision

## Database Schemas

### MySQL Database (blog_db)

#### BlogPost Table

```sql
CREATE TABLE blog_posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    thread_id VARCHAR(255) UNIQUE NOT NULL,  -- Links to SQLite checkpoint
    topic VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved_at DATETIME NULL,
    rejection_reason TEXT NULL
);
```

### SQLite Database (blog_workflow.db)

**Auto-managed by LangGraph, contains:**
- `checkpoints` table: Workflow states indexed by thread_id
- `checkpoint_writes` table: State update history
- Internal LangGraph checkpoint schema

**You can inspect it with:**
```bash
sqlite3 blog_workflow.db
.tables
.schema checkpoints
SELECT * FROM checkpoints;
```

## Configuration

### Change LLM Model

Edit `blog_agents.py`:

```python
llm = ChatOllama(
    model="qwen2.5:0.5b",  # Change to: llama3.2:1b, mistral:latest, etc.
    temperature=0.7,
)
```

**Recommended Models:**
- `qwen2.5:0.5b` - Fastest (20-30 seconds)
- `llama3.2:1b` - Balanced (40-60 seconds)
- `mistral:latest` - Best quality (60-90 seconds)

### Change Database Settings

Edit `.env` file:

```env
DATABASE=blog_db
PASSWORD=your_mysql_password
```

Or directly edit `database.py`:

```python
DATABASE_URL = "mysql+pymysql://root:YOUR_PASSWORD@localhost/blog_db"
```

## Troubleshooting

**Database Connection Error (MySQL):**
- Verify MySQL is running: `mysql -u root -p`
- Check username/password in `.env` file
- Ensure `blog_db` database exists
- Run `python setup_database.py` to recreate

**Checkpoint Database Issues:**
- `blog_workflow.db` is auto-created by LangGraph
- If corrupted, delete it and restart server
- Each thread_id creates one checkpoint entry
- Database uses `check_same_thread=False` for multi-process access

**Workflow Not Pausing:**
- Check console logs for `[GENERATE] ✓ Workflow paused at checkpoint`
- Verify `interrupt_before=["human_approval"]` in `blog_agents.py`
- Ensure `langgraph-checkpoint-sqlite` is installed
- Check LangGraph version: `pip show langgraph`

**Workflow Not Resuming:**
- Verify thread_id matches between MySQL and SQLite
- Check console logs for `[RESUME] Resuming workflow execution`
- Ensure `update_state(as_node="human_approval")` is called
- Check for errors in workflow state

**Ollama Connection Error:**
- Make sure Ollama is running: `ollama serve`
- Verify model is installed: `ollama list`
- Pull model if missing: `ollama pull qwen2.5:0.5b`

**Generation Takes Too Long:**
- Use a smaller model (qwen2.5:0.5b) for faster results
- Check Ollama server load: `ollama ps`
- Ensure sufficient RAM/CPU resources

**Approval Status Not Updating:**
- Check browser console for JavaScript errors
- Verify API endpoint is accessible: `http://localhost:8000/api/stats`
- Check if workflow checkpoint exists in SQLite
- Clear browser cache and reload

**Stats Not Refreshing:**
- Stats auto-refresh every 30 seconds
- Click "Refresh" button to manually update
- Check network tab for failed requests

## Verification Steps

After setup, verify HITL is working:

1. **Check Console Logs During Generation:**
   ```
   [GENERATE] Starting blog generation (STEP 1: Before Human)
   [AGENT] Research Agent: Creating outline...
   [AGENT] Title Agent: Generating title...
   [AGENT] Writer Agent: Writing blog...
   [AGENT] Editor Agent: Refining content...
   [GENERATE] ✓ Workflow paused at checkpoint
   [GENERATE] Next node to execute: ('human_approval',)
   [GENERATE] Waiting for human decision...
   ```

2. **Check SQLite Database Created:**
   ```bash
   ls -la blog_workflow.db
   ```

3. **Verify Checkpoint on Approval:**
   ```
   [UPDATE] Human decision received (STEP 2: Human Input)
   [UPDATE] Calling update_state(as_node='human_approval')...
   [UPDATE] ✓ State updated successfully
   [RESUME] Resuming workflow execution (STEP 3: After Human)
   [ROUTER] Checking approval status: approved
   [FINAL] ✓ Blog APPROVED
   [RESUME] ✓ Workflow completed
   ```

## Advanced Features

### Workflow State Inspection

Get current workflow state for a blog:

```bash
curl http://localhost:8000/api/blogs/1/state
```

Response shows:
- Current approval status
- Next nodes to execute
- Whether workflow is paused

### Concurrent Workflows

The HITL system supports multiple simultaneous blog generations:
- Each has unique thread_id
- Independent checkpoints in SQLite
- No interference between workflows
- All can pause at human approval independently

### Server Restart Recovery

**Workflow state persists across restarts:**
1. Generate blog → workflow pauses
2. Stop server (`Ctrl+C`)
3. Restart server (`python main.py`)
4. Approve/reject blog → workflow resumes correctly

This works because:
- SQLite checkpoint saved to disk
- MySQL blog record preserved
- thread_id links them together

## Best Practices

### HITL Workflow
1. **Regular Checkpoint Review**: Monitor pending workflows in SQLite
2. **Timely Reviews**: Don't leave workflows paused too long
3. **Clear Rejection Reasons**: Helps improve future prompts
4. **Workflow Monitoring**: Check console logs for checkpoint issues

### Database Management
1. **SQLite Cleanup**: Periodically remove old checkpoints
2. **MySQL Archival**: Archive old approved/rejected blogs
3. **Thread ID Tracking**: Keep thread_ids synchronized
4. **Backup Both Databases**: Critical for recovery

### Performance
1. **Limit Concurrent Workflows**: Depends on server resources
2. **Monitor Checkpoint Size**: SQLite grows with workflows
3. **Optimize LLM Calls**: Smaller models for faster checkpoints

## Future Enhancements

### HITL Improvements
- [ ] Multi-level approval (reviewer → editor → publisher)
- [ ] Approval delegation and routing
- [ ] Workflow timeout handling
- [ ] Checkpoint cleanup automation
- [ ] Workflow versioning

### Core Features
- [ ] Blog editing functionality for approved blogs
- [ ] User authentication and role-based access
- [ ] Bulk approve/reject operations
- [ ] Blog versioning and revision history
- [ ] Re-generation from rejected blogs

### Content Features
- [ ] Blog categories and tags
- [ ] SEO score and optimization suggestions
- [ ] Plagiarism checking
- [ ] Export to PDF/Markdown/HTML
- [ ] AI-generated images for blog posts
- [ ] Scheduled publishing for approved blogs

### Workflow Features
- [ ] Email notifications for pending approvals
- [ ] Approval deadline tracking with automatic timeout
- [ ] Comment/feedback system for rejections
- [ ] Approval analytics and reporting
- [ ] Workflow visualization dashboard

## API Response Examples

### Generate Blog (Creates Checkpoint)

**Request:**
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Future of AI"}'
```

**Response:**
```json
{
  "id": 1,
  "thread_id": "blog_abc123",
  "topic": "Future of AI",
  "title": "The Future of AI: Transforming Tomorrow",
  "content": "...",
  "status": "pending",
  "created_at": "2026-01-22T10:30:00",
  "approved_at": null,
  "rejection_reason": null
}
```

### Check Workflow State

**Request:**
```bash
curl http://localhost:8000/api/blogs/1/state
```

**Response:**
```json
{
  "topic": "Future of AI",
  "title": "The Future of AI: Transforming Tomorrow",
  "content": "...",
  "approval_status": "pending",
  "rejection_reason": "",
  "next_nodes": ["human_approval"],
  "thread_id": "blog_abc123"
}
```

### Approve Blog (Resumes Workflow)

**Request:**
```bash
curl -X POST http://localhost:8000/api/blogs/1/review \
  -H "Content-Type: application/json" \
  -d '{"action": "approve"}'
```

**Response:**
```json
{
  "id": 1,
  "thread_id": "blog_abc123",
  "topic": "Future of AI",
  "title": "The Future of AI: Transforming Tomorrow",
  "content": "...",
  "status": "approved",
  "created_at": "2026-01-22T10:30:00",
  "approved_at": "2026-01-22T11:45:00",
  "rejection_reason": null
}
```

### Reject Blog (Resumes Workflow)

**Request:**
```bash
curl -X POST http://localhost:8000/api/blogs/1/review \
  -H "Content-Type: application/json" \
  -d '{
    "action": "reject",
    "rejection_reason": "Content lacks depth and specific examples"
  }'
```

**Response:**
```json
{
  "id": 1,
  "thread_id": "blog_abc123",
  "topic": "Future of AI",
  "title": "The Future of AI: Transforming Tomorrow",
  "content": "...",
  "status": "rejected",
  "created_at": "2026-01-22T10:30:00",
  "approved_at": null,
  "rejection_reason": "Content lacks depth and specific examples"
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - Feel free to use and modify for your projects!

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review HITL verification steps
3. Inspect `blog_workflow.db` for checkpoint issues
4. Check Ollama and MySQL logs
5. Open an issue on GitHub

---

**Built with ❤️ using LangChain, LangGraph, FastAPI, MySQL, and SQLite**

**Powered by Human-in-the-Loop (HITL) pattern for production-ready AI workflows**
