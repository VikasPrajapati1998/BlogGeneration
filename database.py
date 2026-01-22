from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from urllib.parse import quote_plus
import enum
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database credentials from .env
DB_NAME = os.getenv("DATABASE", "blog_db")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("PASSWORD", "abcd@1234")
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = os.getenv("DB_PORT", "3306")

DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)

# Database URL format
# DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f"Connecting to database: {DB_NAME} at {DB_HOST}")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20, pool_recycle=3600, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ApprovalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class BlogPost(Base):
    __tablename__ = "blog_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(255), nullable=False, unique=True, index=True)
    topic = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(ApprovalStatus, native_enum=False, length=20), default=ApprovalStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

