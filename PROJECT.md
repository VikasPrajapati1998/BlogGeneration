# AI Blog Generator - Project Documentation

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Flow Diagrams](#flow-diagrams)
3. [LangGraph Agent Workflow](#langgraph-agent-workflow)
4. [Database Schema](#database-schema)
5. [API Flow](#api-flow)
6. [Execution Flow](#execution-flow)
7. [Component Interaction](#component-interaction)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ index.html   │  │  style.css   │  │     script.js        │   │
│  │              │  │              │  │  - Event Handlers    │   │
│  │ - UI Layout  │  │ - Styling    │  │  - API Calls         │   │
│  │ - Forms      │  │ - Responsive │  │  - State Management  │   │
│  │ - Stats      │  │ - Animations │  │  - DOM Manipulation  │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST API
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI Server)                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                        main.py                           │   │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐   │   │
│  │  │  Endpoints │  │  Middleware  │  │  Lifespan Mgmt  │   │   │
│  │  │            │  │              │  │                 │   │   │
│  │  │ /generate  │  │  CORS        │  │  init_db()      │   │   │
│  │  │ /blogs     │  │  Static      │  │                 │   │   │
│  │  │ /review    │  │  Files       │  │                 │   │   │
│  │  │ /stats     │  │              │  │                 │   │   │
│  │  └────────────┘  └──────────────┘  └─────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────┬──────────────────────────┬──────────────────────────┘
            │                          │
            ↓                          ↓
┌───────────────────────┐   ┌──────────────────────────────┐
│   database.py         │   │     blog_agents.py           │
│                       │   │                              │
│  ┌────────────────┐   │   │  ┌────────────────────────┐  │
│  │ SQLAlchemy ORM │   │   │  │  LangGraph Workflow    │  │
│  │                │   │   │  │                        │  │
│  │ - BlogPost     │   │   │  │  ┌──────────────────┐  │  │
│  │ - ApprovalStatus│  │   │  │  │ Research Agent   │  │  │ 
│  │ - Session Mgmt │   │   │  │  ├──────────────────┤  │  │
│  └────────────────┘   │   │  │  │ Title Agent      │  │  │
│                       │   │  │  ├──────────────────┤  │  │
└───────┬───────────────┘   │  │  │ Writer Agent     │  │  │
        │                   │  │  ├──────────────────┤  │  │
        ↓                   │  │  │ Editor Agent     │  │  │
┌───────────────────────┐   │  │  └──────────────────┘  │  │
│   MySQL Database      │   │  └────────────────────────┘  │
│                       │   │             │                │
│  ┌────────────────┐   │   │             ↓                │
│  │  blog_posts    │   │   │  ┌────────────────────────┐  │
│  │                │   │   │  │  Ollama LLM (Local)    │  │
│  │  - id          │   │   │  │  qwen2.5:0.5b          │  │
│  │  - topic       │   │   │  └────────────────────────┘  │
│  │  - title       │   │   └──────────────────────────────┘
│  │  - content     │   │
│  │  - status      │   │
│  │  - created_at  │   │
│  │  - approved_at │   │
│  │  - rejection   │   │
│  └────────────────┘   │
└───────────────────────┘
```

---

## Flow Diagrams

### 1. Blog Generation Flow

```
┌─────────────┐
│   User      │
│  Enters     │
│   Topic     │
└──────┬──────┘
       │
       ↓
┌──────────────────────────────────────────────┐
│         Frontend (script.js)                 │
│  1. Validate input                           │
│  2. Show loading indicator                   │
│  3. POST /api/generate                       │
└──────┬───────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────┐
│         Backend (main.py)                    │
│  1. Receive topic request                    │
│  2. Call generate_blog(topic)                │
└──────┬───────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────┐
│      LangGraph Workflow (blog_agents.py)     │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  Step 1: Research Agent                │  │
│  │  - Analyze topic                       │  │
│  │  - Create outline                      │  │
│  │  - Return: state["outline"]            │  │
│  └────────────┬───────────────────────────┘  │
│               ↓                              │
│  ┌────────────────────────────────────────┐  │
│  │  Step 2: Title Agent                   │  │
│  │  - Generate SEO-friendly title         │  │
│  │  - Return: state["title"]              │  │
│  └────────────┬───────────────────────────┘  │
│               ↓                              │
│  ┌────────────────────────────────────────┐  │
│  │  Step 3: Writer Agent                  │  │
│  │  - Write full blog post                │  │
│  │  - Use outline and title               │  │
│  │  - Return: state["content"]            │  │
│  └────────────┬───────────────────────────┘  │
│               ↓                              │
│  ┌────────────────────────────────────────┐  │
│  │  Step 4: Editor Agent                  │  │
│  │  - Refine content                      │  │
│  │  - Fix grammar                         │  │
│  │  - Return: state["refined_content"]    │  │
│  └────────────┬───────────────────────────┘  │
│               │                              │
└───────────────┼──────────────────────────────┘
                ↓
┌──────────────────────────────────────────────┐
│         Backend (main.py)                    │
│  1. Create BlogPost object                   │
│  2. Set status = PENDING                     │
│  3. Save to MySQL database                   │
│  4. Return blog data as JSON                 │
└──────┬───────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────┐
│         Frontend (script.js)                 │
│  1. Hide loading indicator                   │
│  2. Display generated blog                   │
│  3. Show review buttons (Approve/Reject)     │
│  4. Update stats dashboard                   │
│  5. Refresh blog list                        │
└──────────────────────────────────────────────┘
```

### 2. Approval Workflow

```
┌─────────────────────────────────────────────────────────┐
│                    PENDING BLOG                         │
│  Status: pending | Created: [timestamp]                 │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ↓                           ↓
┌──────────────────┐         ┌──────────────────┐
│   APPROVE        │         │    REJECT        │
│   Button Click   │         │   Button Click   │
└────────┬─────────┘         └────────┬─────────┘
         │                            │
         │                            ↓
         │                   ┌─────────────────┐
         │                   │  Rejection      │
         │                   │  Modal Opens    │
         │                   │  - Enter Reason │
         │                   └────────┬────────┘
         │                            │
         ↓                            ↓
┌────────────────────────────────────────────────┐
│     POST /api/blogs/{id}/review                │
│                                                │
│  Approve: {"action": "approve"}                │
│  Reject: {                                     │
│    "action": "reject",                         │
│    "rejection_reason": "..."                   │
│  }                                             │
└────────┬───────────────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────────────┐
│         Backend Processing (main.py)           │
│                                                │
│  1. Validate blog exists                       │
│  2. Check status is PENDING                    │
│  3. If APPROVE:                                │
│     - Set status = APPROVED                    │
│     - Set approved_at = current_timestamp      │
│  4. If REJECT:                                 │
│     - Set status = REJECTED                    │
│     - Set rejection_reason = reason_text       │
│  5. db.commit()                                │
└────────┬───────────────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────────────┐
│            Update Database                     │
│                                                │
│  UPDATE blog_posts SET                         │
│    status = 'approved'/'rejected',             │
│    approved_at = NOW() (if approved),          │
│    rejection_reason = '...' (if rejected)      │
│  WHERE id = {blog_id}                          │
└────────┬───────────────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────────────┐
│         Frontend Updates                       │
│                                                │
│  1. Update status badge                        │
│  2. Hide review buttons                        │
│  3. Show approved_at timestamp (if approved)   │
│  4. Show rejection reason (if rejected)        │
│  5. Refresh stats dashboard                    │
│  6. Refresh blog list                          │
└────────────────────────────────────────────────┘
```

### 3. Complete User Journey

```
START
  │
  ├─→ User Opens App (http://localhost:8000)
  │     │
  │     ├─→ Load Statistics (GET /api/stats)
  │     │     └─→ Display: Total, Pending, Approved, Rejected
  │     │
  │     └─→ Load All Blogs (GET /api/blogs)
  │           └─→ Display blog list
  │
  ├─→ User Enters Topic & Clicks "Generate"
  │     │
  │     ├─→ Validation
  │     │
  │     ├─→ Show Loading (30-60 seconds)
  │     │     └─→ Step indicators: Research → Title → Write → Edit
  │     │
  │     ├─→ POST /api/generate
  │     │     │
  │     │     ├─→ LangGraph Workflow Executes
  │     │     │     ├─→ Research Agent → Outline
  │     │     │     ├─→ Title Agent → Title
  │     │     │     ├─→ Writer Agent → Content
  │     │     │     └─→ Editor Agent → Refined Content
  │     │     │
  │     │     ├─→ Save to Database (status: PENDING)
  │     │     │
  │     │     └─→ Return Blog Data
  │     │
  │     └─→ Display Generated Blog
  │           ├─→ Show Title, Topic, Content
  │           ├─→ Show Status Badge: PENDING
  │           └─→ Show Review Buttons: Approve | Reject
  │
  ├─→ User Reviews Blog
  │     │
  │     ├─→ OPTION A: Approve
  │     │     ├─→ Confirmation Dialog
  │     │     ├─→ POST /api/blogs/{id}/review
  │     │     │     └─→ {"action": "approve"}
  │     │     ├─→ Update Database
  │     │     └─→ Display: Status = APPROVED, Timestamp
  │     │
  │     └─→ OPTION B: Reject
  │           ├─→ Open Rejection Modal
  │           ├─→ Enter Rejection Reason
  │           ├─→ POST /api/blogs/{id}/review
  │           │     └─→ {"action": "reject", "rejection_reason": "..."}
  │           ├─→ Update Database
  │           └─→ Display: Status = REJECTED, Reason
  │
  ├─→ User Filters Blogs
  │     │
  │     ├─→ Click "All" Tab → GET /api/blogs
  │     ├─→ Click "Pending" Tab → GET /api/blogs?status=pending
  │     ├─→ Click "Approved" Tab → GET /api/blogs?status=approved
  │     └─→ Click "Rejected" Tab → GET /api/blogs?status=rejected
  │
  ├─→ User Views Full Blog
  │     └─→ Click "View Full" → GET /api/blogs/{id}
  │           └─→ Display complete blog with status
  │
  ├─→ User Deletes Blog
  │     └─→ Click "Delete" → DELETE /api/blogs/{id}
  │           ├─→ Confirmation Dialog
  │           ├─→ Remove from Database
  │           └─→ Refresh List & Stats
  │
  └─→ Stats Auto-Refresh (Every 10 seconds)
        └─→ GET /api/stats
              └─→ Update Dashboard Numbers
```

---

## LangGraph Agent Workflow

### State Graph Visualization

```
                    ┌─────────────────────┐
                    │   INITIAL STATE     │
                    │                     │
                    │  topic: "..."       │
                    │  title: ""          │
                    │  outline: ""        │
                    │  content: ""        │
                    │  refined_content: ""│
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │  RESEARCH AGENT     │
                    │  (do_research)      │
                    │                     │
                    │  Input: topic       │
                    │  Process:           │
                    │  - Analyze topic    │
                    │  - Create outline   │
                    │  Output: outline    │
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │   TITLE AGENT       │
                    │  (generate_title)   │
                    │                     │
                    │  Input: topic       │
                    │  Process:           │
                    │  - Generate title   │
                    │  Output: title      │
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │  WRITER AGENT       │
                    │  (write_blog)       │
                    │                     │
                    │  Input:             │
                    │  - topic            │
                    │  - title            │
                    │  - outline          │
                    │  Process:           │
                    │  - Write blog post  │
                    │  Output: content    │
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │  EDITOR AGENT       │
                    │  (edit_blog)        │
                    │                     │
                    │  Input:             │
                    │  - title            │
                    │  - content          │
                    │  Process:           │
                    │  - Fix grammar      │
                    │  - Improve clarity  │
                    │  Output:            │
                    │    refined_content  │
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │      END            │
                    │                     │
                    │  Final State:       │
                    │  - topic            │
                    │  - title            │
                    │  - refined_content  │
                    └─────────────────────┘
```

### Agent Communication Pattern

```
Agent 1 (Research)
    ↓
[State Update] → state["outline"] = "..."
    ↓
Agent 2 (Title)
    ↓
[State Update] → state["title"] = "..."
    ↓
Agent 3 (Writer)
    ↓
[State Update] → state["content"] = "..."
    ↓
Agent 4 (Editor)
    ↓
[State Update] → state["refined_content"] = "..."
    ↓
Return to main.py
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────┐
│                  blog_posts                     │
├─────────────────────────────────────────────────┤
│ PK │ id                INT AUTO_INCREMENT       │
│    │ topic             VARCHAR(255) NOT NULL    │
│    │ title             VARCHAR(500) NOT NULL    │
│    │ content           TEXT NOT NULL            │
│    │ status            ENUM NOT NULL            │
│    │                   ('pending',              │
│    │                    'approved',             │
│    │                    'rejected')             │
│    │                   DEFAULT 'pending'        │
│    │ created_at        DATETIME                 │
│    │                   DEFAULT CURRENT_TIMESTAMP│
│    │ approved_at       DATETIME NULL            │
│    │ rejection_reason  TEXT NULL                │
└─────────────────────────────────────────────────┘

Indexes:
  - PRIMARY KEY (id)
  - INDEX (status)
  - INDEX (created_at)

Constraints:
  - status must be one of: pending, approved, rejected
  - approved_at is set only when status = approved
  - rejection_reason is set only when status = rejected
```

### Status State Machine

```
         ┌─────────┐
         │ PENDING │ ← Initial state for all new blogs
         └────┬────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ↓                   ↓
┌──────────┐      ┌──────────┐
│ APPROVED │      │ REJECTED │
└──────────┘      └──────────┘
  (Final)           (Final)

Rules:
- PENDING → APPROVED (with approved_at timestamp)
- PENDING → REJECTED (with rejection_reason)
- APPROVED/REJECTED cannot change status
```

---

## API Flow

### API Endpoint Map

```
┌──────────────────────────────────────────────────────────┐
│                     API ENDPOINTS                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  PUBLIC ENDPOINTS                                        │
│  ├─ GET  /                → Serve index.html             │
│  ├─ GET  /health          → Health check                 │
│  └─ GET  /static/*        → Static files                 │
│                                                          │
│  BLOG GENERATION                                         │
│  └─ POST /api/generate    → Generate new blog            │
│      Request:  {"topic": "string"}                       │
│      Response: BlogResponse (status: pending)            │
│                                                          │
│  BLOG RETRIEVAL                                          │
│  ├─ GET  /api/blogs       → Get all blogs                │
│  │   Query: ?status=pending|approved|rejected            │
│  │   Response: List[BlogResponse]                        │
│  │                                                       │
│  └─ GET  /api/blogs/{id}  → Get specific blog            │
│      Response: BlogResponse                              │
│                                                          │
│  BLOG REVIEW                                             │
│  └─ POST /api/blogs/{id}/review → Approve/Reject         │
│      Request:                                            │
│        {"action": "approve"}                             │
│        OR                                                │
│        {"action": "reject",                              │
│         "rejection_reason": "string"}                    │
│      Response: BlogResponse (updated status)             │
│                                                          │
│  BLOG MANAGEMENT                                         │
│  └─ DELETE /api/blogs/{id} → Delete blog                 │
│      Response: {"message": "Blog deleted successfully"}  │
│                                                          │
│  STATISTICS                                              │
│  └─ GET /api/stats         → Get approval statistics     │
│      Response: {                                         │
│        "total": int,                                     │
│        "pending": int,                                   │
│        "approved": int,                                  │
│        "rejected": int                                   │
│      }                                                   │
└──────────────────────────────────────────────────────────┘
```

### Request-Response Flow Example

```
POST /api/generate
─────────────────────────────────────────────────────
Request:
{
  "topic": "Future of AI"
}

Backend Processing:
1. Validate topic
2. Call generate_blog(topic)
   ├─ LangGraph executes 4 agents
   └─ Returns: {topic, title, content}
3. Create BlogPost with status=PENDING
4. Save to database
5. Generate response

Response (200 OK):
{
  "id": 1,
  "topic": "Future of AI",
  "title": "The Future of AI: Transforming Tomorrow",
  "content": "...[full blog content]...",
  "status": "pending",
  "created_at": "2026-01-22T10:30:00",
  "approved_at": null,
  "rejection_reason": null
}

─────────────────────────────────────────────────────

POST /api/blogs/1/review
─────────────────────────────────────────────────────
Request:
{
  "action": "approve"
}

Backend Processing:
1. Get blog with id=1
2. Validate status is PENDING
3. Set status = APPROVED
4. Set approved_at = NOW()
5. Save to database

Response (200 OK):
{
  "id": 1,
  "topic": "Future of AI",
  "title": "The Future of AI: Transforming Tomorrow",
  "content": "...[full blog content]...",
  "status": "approved",
  "created_at": "2026-01-22T10:30:00",
  "approved_at": "2026-01-22T11:45:00",
  "rejection_reason": null
}
```

---

## Execution Flow

### Application Startup Sequence

```
1. python main.py
   │
   ├─→ Load environment variables (.env)
   │    ├─ LANGCHAIN_TRACING_V2
   │    ├─ LANGCHAIN_API_KEY
   │    ├─ DATABASE credentials
   │    └─ PASSWORD
   │
   ├─→ Initialize FastAPI app
   │    ├─ Set up CORS middleware
   │    ├─ Mount static files (/static)
   │    └─ Register lifespan events
   │
   ├─→ Lifespan Startup
   │    └─ init_db()
   │         ├─ Create database engine
   │         ├─ Create all tables
   │         │   └─ blog_posts table with approval fields
   │         └─ Print "Application ready!"
   │
   ├─→ Import blog_agents.py
   │    ├─ Initialize ChatOllama LLM
   │    ├─ Define BlogState TypedDict
   │    ├─ Create agent functions
   │    └─ Build LangGraph workflow
   │
   ├─→ Start Uvicorn server
   │    ├─ Host: 0.0.0.0
   │    ├─ Port: 8000
   │    └─ Reload: False (production)
   │
   └─→ Server Ready
        └─ Listening on http://localhost:8000
```

### Runtime Execution Flow

```
USER ACTION: Generate Blog
────────────────────────────────────────────────

1. Frontend Event (script.js)
   │
   ├─→ User types topic: "Future of AI"
   ├─→ User clicks "Generate Blog"
   ├─→ Form validation passes
   ├─→ UI: Show loading spinner
   ├─→ UI: Animate progress steps
   │
   └─→ fetch('/api/generate', {
         method: 'POST',
         body: JSON.stringify({topic: "Future of AI"})
       })

2. Network Layer
   │
   └─→ HTTP POST request to backend

3. FastAPI Router (main.py)
   │
   ├─→ Route: /api/generate
   ├─→ Handler: create_blog()
   ├─→ Parse request: BlogRequest
   └─→ Extract: topic = "Future of AI"

4. Blog Generation (blog_agents.py)
   │
   ├─→ Call: generate_blog("Future of AI")
   ├─→ Create workflow: create_blog_workflow()
   ├─→ Initialize state: BlogState
   │
   └─→ Execute LangGraph workflow
       │
       ├─→ Node: do_research (Research Agent)
       │    ├─ Prompt: "Create outline for: Future of AI"
       │    ├─ Call Ollama LLM
       │    ├─ Response time: ~5-10 seconds
       │    └─ state["outline"] = "I. Introduction\nII. Current State..."
       │
       ├─→ Node: generate_title (Title Agent)
       │    ├─ Prompt: "Create SEO title for: Future of AI"
       │    ├─ Call Ollama LLM
       │    ├─ Response time: ~3-5 seconds
       │    └─ state["title"] = "The Future of AI: Transforming Tomorrow"
       │
       ├─→ Node: write_blog (Writer Agent)
       │    ├─ Prompt: "Write blog with title and outline"
       │    ├─ Call Ollama LLM
       │    ├─ Response time: ~15-20 seconds
       │    └─ state["content"] = "[Full blog content...]"
       │
       └─→ Node: edit_blog (Editor Agent)
            ├─ Prompt: "Edit and refine blog content"
            ├─ Call Ollama LLM
            ├─ Response time: ~10-15 seconds
            └─ state["refined_content"] = "[Polished content...]"

5. Database Persistence (main.py)
   │
   ├─→ Create BlogPost object
   │    ├─ topic: "Future of AI"
   │    ├─ title: "The Future of AI: Transforming Tomorrow"
   │    ├─ content: state["refined_content"]
   │    ├─ status: ApprovalStatus.PENDING
   │    └─ created_at: NOW()
   │
   ├─→ db.add(blog_post)
   ├─→ db.commit()
   └─→ db.refresh(blog_post)
        └─ blog_post.id = 1

6. Response Generation
   │
   ├─→ Create BlogResponse
   │    ├─ id: 1
   │    ├─ topic: "Future of AI"
   │    ├─ title: "..."
   │    ├─ content: "..."
   │    ├─ status: "pending"
   │    ├─ created_at: "2026-01-22T10:30:00"
   │    ├─ approved_at: null
   │    └─ rejection_reason: null
   │
   └─→ Return JSON response

7. Frontend Update (script.js)
   │
   ├─→ Receive response
   ├─→ UI: Hide loading spinner
   ├─→ displayGeneratedBlog(blog)
   │    ├─ Show title
   │    ├─ Show content
   │    ├─ Show status badge: PENDING
   │    └─ Show review buttons: Approve | Reject
   │
   ├─→ loadAllBlogs()
   │    └─ Refresh blog list
   │
   └─→ loadStats()
        └─ Update dashboard: Pending +1

Total Time: ~35-50 seconds
```

### Approval Execution Flow

```
USER ACTION: Approve Blog
────────────────────────────────────────────────

1. Frontend Event
   │
   ├─→ User clicks "✓ Approve Blog"
   ├─→ Confirmation dialog: "Are you sure?"
   ├─→ User confirms
   │
   └─→ fetch('/api/blogs/1/review', {
         method: 'POST',
         body: JSON.stringify({action: "approve"})
       })
