from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import uvicorn
import os
import uuid
from dotenv import load_dotenv

from database import get_db, init_db, BlogPost, ApprovalStatus
from blog_agents import generate_blog, update_approval_status, get_blog_state

# Load environment variables
load_dotenv()

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Blog Generation API...")
    init_db()
    print("Application ready!")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Blog Generation API",
    description="AI-powered blog generation using LangChain and LangGraph with HITL",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class BlogRequest(BaseModel):
    topic: str

class ApprovalRequest(BaseModel):
    action: str  # "approve" or "reject"
    rejection_reason: Optional[str] = None

class BlogResponse(BaseModel):
    id: int
    thread_id: str
    topic: str
    title: str
    content: str
    status: str
    created_at: str
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the frontend"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: index.html not found in static folder</h1>"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "langchain_project": os.getenv("LANGCHAIN_PROJECT"),
        "database": os.getenv("DATABASE")
    }

def generate_blog_async(topic: str, thread_id: str, blog_id: int):
    """Background task to generate blog - uses separate DB session"""
    from database import SessionLocal
    db = SessionLocal()
    
    try:
        print(f"\n[Background] Starting blog generation for thread: {thread_id}")
        blog_data = generate_blog(topic, thread_id)
        
        # Update the blog post in database with generated content
        blog_post = db.query(BlogPost).filter(BlogPost.id == blog_id).first()
        if blog_post:
            blog_post.title = blog_data["title"]
            blog_post.content = blog_data["content"]
            blog_post.status = ApprovalStatus.PENDING
            db.commit()
            print(f"[Background] Blog generated successfully: {thread_id}")
            print(f"[Background] Status: PENDING (awaiting human approval)")
    except Exception as e:
        print(f"[Background] Error generating blog: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update status to rejected on error
        blog_post = db.query(BlogPost).filter(BlogPost.id == blog_id).first()
        if blog_post:
            blog_post.status = ApprovalStatus.REJECTED
            blog_post.rejection_reason = f"Generation error: {str(e)}"
            db.commit()
    finally:
        db.close()

@app.post("/api/generate", response_model=BlogResponse)
async def create_blog(
    request: BlogRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start blog generation process (async with HITL checkpoint)"""
    try:
        print(f"\n[API] Received request to generate blog on topic: {request.topic}")
        
        # Generate unique thread ID for this workflow
        thread_id = f"blog_{uuid.uuid4().hex[:16]}"
        
        # Create initial blog post record with PENDING status
        blog_post = BlogPost(
            thread_id=thread_id,
            topic=request.topic,
            title="Generating...",
            content="Blog generation in progress...",
            status=ApprovalStatus.PENDING
        )
        db.add(blog_post)
        db.commit()
        db.refresh(blog_post)
        
        print(f"[API] Blog entry created with ID: {blog_post.id}, thread: {thread_id}")
        print(f"[API] Initial status: PENDING")
        
        # Start blog generation in background - pass blog_id instead of db session
        background_tasks.add_task(generate_blog_async, request.topic, thread_id, blog_post.id)
        
        return BlogResponse(
            id=blog_post.id,
            thread_id=blog_post.thread_id,
            topic=blog_post.topic,
            title=blog_post.title,
            content=blog_post.content,
            status=blog_post.status.value,
            created_at=blog_post.created_at.isoformat(),
            approved_at=blog_post.approved_at.isoformat() if blog_post.approved_at else None,
            rejection_reason=blog_post.rejection_reason
        )
    except Exception as e:
        print(f"[API] Error creating blog: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating blog: {str(e)}")

@app.get("/api/blogs", response_model=List[BlogResponse])
async def get_all_blogs(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all blog posts, optionally filtered by status"""
    try:
        query = db.query(BlogPost)
        
        # Filter by status if provided
        if status:
            if status.lower() in ["pending", "approved", "rejected"]:
                query = query.filter(BlogPost.status == ApprovalStatus[status.upper()])
        
        blogs = query.order_by(BlogPost.created_at.desc()).all()
        
        return [
            BlogResponse(
                id=blog.id,
                thread_id=blog.thread_id,
                topic=blog.topic,
                title=blog.title,
                content=blog.content,
                status=blog.status.value,
                created_at=blog.created_at.isoformat(),
                approved_at=blog.approved_at.isoformat() if blog.approved_at else None,
                rejection_reason=blog.rejection_reason
            )
            for blog in blogs
        ]
    except Exception as e:
        print(f"[API] Error fetching blogs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching blogs: {str(e)}")

@app.get("/api/blogs/{blog_id}", response_model=BlogResponse)
async def get_blog(blog_id: int, db: Session = Depends(get_db)):
    """Get a specific blog post"""
    blog = db.query(BlogPost).filter(BlogPost.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    return BlogResponse(
        id=blog.id,
        thread_id=blog.thread_id,
        topic=blog.topic,
        title=blog.title,
        content=blog.content,
        status=blog.status.value,
        created_at=blog.created_at.isoformat(),
        approved_at=blog.approved_at.isoformat() if blog.approved_at else None,
        rejection_reason=blog.rejection_reason
    )

@app.post("/api/blogs/{blog_id}/review", response_model=BlogResponse)
async def review_blog(
    blog_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Approve or reject a blog post
    This updates the workflow state and resumes execution
    NO POLLING - direct state update with graph.update_state()
    """
    blog = db.query(BlogPost).filter(BlogPost.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    if blog.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Blog is already {blog.status.value}. Only pending blogs can be reviewed."
        )
    
    # Validate action
    if request.action.lower() not in ["approve", "reject"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid action. Use 'approve' or 'reject'"
        )
    
    try:
        print(f"[API] Review request for blog {blog_id}")
        print(f"[API] Thread ID: {blog.thread_id}")
        print(f"[API] Action: {request.action}")
        
        # Update workflow state and resume execution using graph.update_state()
        # This will trigger the workflow to continue from the checkpoint
        result = update_approval_status(
            thread_id=blog.thread_id,
            action=request.action.lower(),
            rejection_reason=request.rejection_reason
        )
        
        print(f"[API] Workflow resumed and completed")
        print(f"[API] Final status: {result['approval_status']}")
        
        # Update database with workflow result
        if result['approval_status'] == "approved":
            blog.status = ApprovalStatus.APPROVED
            blog.approved_at = datetime.now(timezone.utc)
            blog.rejection_reason = None
            print(f"[API] Blog {blog_id} approved")
        elif result['approval_status'] == "rejected":
            blog.status = ApprovalStatus.REJECTED
            blog.rejection_reason = request.rejection_reason or "No reason provided"
            print(f"[API] Blog {blog_id} rejected: {blog.rejection_reason}")
        
        db.commit()
        db.refresh(blog)
        
    except ValueError as e:
        print(f"[API] ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[API] Error in workflow review: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing review: {str(e)}")
    
    return BlogResponse(
        id=blog.id,
        thread_id=blog.thread_id,
        topic=blog.topic,
        title=blog.title,
        content=blog.content,
        status=blog.status.value,
        created_at=blog.created_at.isoformat(),
        approved_at=blog.approved_at.isoformat() if blog.approved_at else None,
        rejection_reason=blog.rejection_reason
    )

@app.delete("/api/blogs/{blog_id}")
async def delete_blog(blog_id: int, db: Session = Depends(get_db)):
    """Delete a blog post"""
    blog = db.query(BlogPost).filter(BlogPost.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    db.delete(blog)
    db.commit()
    print(f"[API] Blog {blog_id} deleted successfully")
    return {"message": "Blog deleted successfully"}

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get statistics about blog posts"""
    total = db.query(BlogPost).count()
    pending = db.query(BlogPost).filter(BlogPost.status == ApprovalStatus.PENDING).count()
    approved = db.query(BlogPost).filter(BlogPost.status == ApprovalStatus.APPROVED).count()
    rejected = db.query(BlogPost).filter(BlogPost.status == ApprovalStatus.REJECTED).count()
    
    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected
    }

@app.get("/api/blogs/{blog_id}/state")
async def get_workflow_state(blog_id: int, db: Session = Depends(get_db)):
    """Get the current workflow state for a blog"""
    blog = db.query(BlogPost).filter(BlogPost.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    state = get_blog_state(blog.thread_id)
    if state is None:
        return {"status": "no_workflow", "message": "No active workflow found"}
    
    return state

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
