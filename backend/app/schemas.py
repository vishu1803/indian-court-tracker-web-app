# backend/app/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum

# Enums for better type safety
class CourtType(str, Enum):
    HIGH_COURT = "HIGH_COURT"
    DISTRICT_COURT = "DISTRICT_COURT"

class CaseStatus(str, Enum):
    PENDING = "PENDING"
    DISPOSED = "DISPOSED"
    ADMITTED = "ADMITTED"
    DISMISSED = "DISMISSED"

class JudgmentType(str, Enum):
    ORDER = "ORDER"
    JUDGMENT = "JUDGMENT"
    NOTICE = "NOTICE"

class QueryStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

# Request schemas
class CaseSearchRequest(BaseModel):
    case_type: str = Field(..., min_length=1, max_length=100, description="Type of case (e.g., WP, CRL)")
    case_number: str = Field(..., min_length=1, max_length=100, description="Case number")
    year: int = Field(..., ge=1950, le=2030, description="Case filing year")
    
    @validator('year')
    def validate_year(cls, v):
        current_year = datetime.now().year
        if v > current_year + 1:
            raise ValueError(f'Year cannot be more than {current_year + 1}')
        return v
    
    @validator('case_type')
    def validate_case_type(cls, v):
        return v.upper().strip()
    
    @validator('case_number')
    def validate_case_number(cls, v):
        return v.strip()

class CauseListRequest(BaseModel):
    hearing_date: date = Field(..., description="Date for which to fetch cause list")
    court_name: Optional[str] = Field(None, description="Specific court name (optional)")
    court_type: Optional[CourtType] = Field(None, description="Court type filter")
    
    @validator('hearing_date')
    def validate_hearing_date(cls, v):
        # Don't allow dates too far in the past or future
        today = date.today()
        if v < date(today.year - 5, 1, 1):
            raise ValueError('Date cannot be more than 5 years in the past')
        if v > date(today.year + 1, 12, 31):
            raise ValueError('Date cannot be more than 1 year in the future')
        return v

# Response schemas
class JudgmentResponse(BaseModel):
    id: int
    judgment_date: Optional[date]
    judgment_type: str
    pdf_url: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    download_status: str
    is_available: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CaseResponse(BaseModel):
    id: int
    parties_petitioner: Optional[str]
    parties_respondent: Optional[str]
    filing_date: Optional[date]
    registration_date: Optional[date]
    next_hearing_date: Optional[date]
    case_status: Optional[str]
    court_name: Optional[str]
    court_type: Optional[str]
    judge_name: Optional[str]
    court_hall: Optional[str]
    case_category: Optional[str]
    case_subcategory: Optional[str]
    disposal_nature: Optional[str]
    data_source: Optional[str]
    last_updated: datetime
    judgments: List[JudgmentResponse] = []

    class Config:
        from_attributes = True

class QueryResponse(BaseModel):
    id: int
    case_type: str
    case_number: str
    year: int
    status: str
    created_at: datetime
    updated_at: datetime
    case: Optional[CaseResponse] = None

    class Config:
        from_attributes = True

class CauseListEntry(BaseModel):
    id: int
    court_name: str
    court_type: str
    case_number: str
    case_type: str
    case_year: Optional[int]
    parties: Optional[str]
    hearing_date: date
    hearing_time: Optional[str]
    court_hall: Optional[str]
    judge_name: Optional[str]
    hearing_purpose: Optional[str]
    case_status_in_list: Optional[str]
    data_source: str
    scraped_at: datetime

    class Config:
        from_attributes = True

class CauseListResponse(BaseModel):
    hearing_date: date
    total_cases: int
    court_wise_count: Dict[str, int]
    entries: List[CauseListEntry]
    cached: bool = False
    last_updated: Optional[datetime] = None

class CaseSearchResponse(BaseModel):
    success: bool
    message: str
    query: QueryResponse
    cached: bool = False
    execution_time_ms: Optional[int] = None

class ScrapingStatsResponse(BaseModel):
    total_queries_today: int
    successful_queries_today: int
    failed_queries_today: int
    cache_hit_rate: float
    average_response_time_ms: float
    redis_stats: Dict[str, Any]

# Utility schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    timestamp: datetime
    version: str = "1.0.0"
