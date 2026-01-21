from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from database import get_db, init_db, BlogPost
from blog_agents import generate_blog

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
    description="AI-powered blog generation using LangChain and LangGraph",
    version="1.0.0",
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

class BlogResponse(BaseModel):
    id: int
    topic: str
    title: str
    content: str
    created_at: str

    class Config:
        from_attributes = True

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

@app.post("/api/generate", response_model=BlogResponse)
async def create_blog(request: BlogRequest, db: Session = Depends(get_db)):
    """Generate a new blog post using AI agents"""
    try:
        print(f"\nReceived request to generate blog on topic: {request.topic}")
        
        # Generate blog using AI agents (REMOVED await - it's a sync function)
        blog_data = generate_blog(request.topic)
        
        # Save to database
        blog_post = BlogPost(
            topic=blog_data["topic"],
            title=blog_data["title"],
            content=blog_data["content"]
        )
        db.add(blog_post)
        db.commit()
        db.refresh(blog_post)
        
        print(f"Blog saved to database with ID: {blog_post.id}")
        
        return BlogResponse(
            id=blog_post.id,
            topic=blog_post.topic,
            title=blog_post.title,
            content=blog_post.content,
            created_at=blog_post.created_at.isoformat()
        )
    except Exception as e:
        print(f"Error generating blog: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating blog: {str(e)}")

@app.get("/api/blogs", response_model=List[BlogResponse])
async def get_all_blogs(db: Session = Depends(get_db)):
    """Get all blog posts"""
    try:
        blogs = db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()
        return [
            BlogResponse(
                id=blog.id,
                topic=blog.topic,
                title=blog.title,
                content=blog.content,
                created_at=blog.created_at.isoformat()
            )
            for blog in blogs
        ]
    except Exception as e:
        print(f"Error fetching blogs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching blogs: {str(e)}")

@app.get("/api/blogs/{blog_id}", response_model=BlogResponse)
async def get_blog(blog_id: int, db: Session = Depends(get_db)):
    """Get a specific blog post"""
    blog = db.query(BlogPost).filter(BlogPost.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    return BlogResponse(
        id=blog.id,
        topic=blog.topic,
        title=blog.title,
        content=blog.content,
        created_at=blog.created_at.isoformat()
    )

@app.delete("/api/blogs/{blog_id}")
async def delete_blog(blog_id: int, db: Session = Depends(get_db)):
    """Delete a blog post"""
    blog = db.query(BlogPost).filter(BlogPost.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    db.delete(blog)
    db.commit()
    print(f"Blog {blog_id} deleted successfully")
    return {"message": "Blog deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
