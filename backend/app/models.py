# backend/app/models.py
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model for optional authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    queries = relationship("Query", back_populates="user")

class Query(Base):
    """Stores user search queries"""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    case_type = Column(String(100), index=True)
    case_number = Column(String(100), index=True)
    year = Column(Integer, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="pending")  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="queries")
    case = relationship("Case", back_populates="query", uselist=False)
    
    # Create compound index for faster searches
    __table_args__ = (
        Index('idx_case_search', 'case_type', 'case_number', 'year'),
    )

class Case(Base):
    """Stores case details scraped from eCourts"""
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id"))
    
    # Case details
    parties_petitioner = Column(Text)
    parties_respondent = Column(Text)
    filing_date = Column(Date, nullable=True)
    registration_date = Column(Date, nullable=True)
    next_hearing_date = Column(Date, nullable=True)
    case_status = Column(String(200))
    
    # Court information
    court_name = Column(String(300))
    court_type = Column(String(50))  # HIGH_COURT, DISTRICT_COURT
    judge_name = Column(String(200), nullable=True)
    court_hall = Column(String(100), nullable=True)
    
    # Additional details
    case_category = Column(String(100), nullable=True)
    case_subcategory = Column(String(100), nullable=True)
    disposal_nature = Column(String(200), nullable=True)
    
    # Metadata
    data_source = Column(String(50))  # HIGH_COURT_PORTAL, DISTRICT_COURT_PORTAL
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    query = relationship("Query", back_populates="case")
    judgments = relationship("Judgment", back_populates="case", cascade="all, delete-orphan")

class Judgment(Base):
    """Stores judgment/order documents"""
    __tablename__ = "judgments"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    
    # Judgment details
    judgment_date = Column(Date)
    judgment_type = Column(String(50))  # ORDER, JUDGMENT, NOTICE
    pdf_url = Column(Text)
    file_name = Column(String(300))
    file_size = Column(Integer, nullable=True)  # in bytes
    
    # Document content (for search functionality)
    content_text = Column(Text, nullable=True)  # Extracted PDF text
    
    # Status tracking
    download_status = Column(String(50), default="pending")  # pending, downloaded, failed
    is_available = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    case = relationship("Case", back_populates="judgments")

class CauseList(Base):
    """Stores daily cause list entries"""
    __tablename__ = "cause_list"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Court information
    court_name = Column(String(300), index=True)
    court_type = Column(String(50), index=True)  # HIGH_COURT, DISTRICT_COURT
    
    # Case information
    case_number = Column(String(100), index=True)
    case_type = Column(String(100), index=True)
    case_year = Column(Integer, index=True)
    parties = Column(Text)
    
    # Hearing details
    hearing_date = Column(Date, index=True)
    hearing_time = Column(String(50), nullable=True)
    court_hall = Column(String(100), nullable=True)
    judge_name = Column(String(200), nullable=True)
    
    # Additional information
    hearing_purpose = Column(String(200), nullable=True)
    case_status_in_list = Column(String(100), nullable=True)
    
    # Metadata
    data_source = Column(String(50))  # HIGH_COURT_PORTAL, DISTRICT_COURT_PORTAL
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Create compound indexes for efficient queries
    __table_args__ = (
        Index('idx_hearing_date_court', 'hearing_date', 'court_name'),
        Index('idx_case_cause_list', 'case_number', 'case_type', 'case_year'),
    )

class ScrapingLog(Base):
    """Logs scraping activities for monitoring"""
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Scraping details
    scraping_type = Column(String(50))  # CASE_SEARCH, CAUSE_LIST
    target_url = Column(Text)
    status = Column(String(50))  # SUCCESS, FAILED, PARTIAL
    
    # Request details
    case_type = Column(String(100), nullable=True)
    case_number = Column(String(100), nullable=True)
    case_year = Column(Integer, nullable=True)
    hearing_date = Column(Date, nullable=True)
    
    # Results
    records_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Integer, nullable=True)  # in milliseconds
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for monitoring queries
    __table_args__ = (
        Index('idx_scraping_status', 'scraping_type', 'status', 'created_at'),
    )
