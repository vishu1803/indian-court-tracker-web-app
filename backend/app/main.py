# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import text  # Add this import at the top
from fastapi.responses import Response
from app.pdf_generator import pdf_generator

from app.config import settings
from app.database import init_db, get_db
from app.redis_client import redis_client
from app.scraper import scraper
from app import models, schemas, crud


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Indian Court Tracker API...")
    
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    if redis_client.is_available():
        logger.info("Redis connection established")
    else:
        logger.warning("Redis connection failed - caching disabled")
    
    yield
    
    logger.info("Shutting down Indian Court Tracker API...")


app = FastAPI(
    title="Indian Court Case & Cause List Tracker",
    description="API for tracking Indian court cases and daily cause lists from official eCourts portals",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Indian Court Case & Cause List Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "features": {
            "case_search": "✅ Implemented with sample data",
            "cause_lists": "✅ Implemented with sample data", 
            "database": "✅ SQLite with SQLAlchemy",
            "caching": "✅ Redis caching" if redis_client.is_available() else "❌ Redis not available",
            "web_scraping": "✅ Playwright-based scraper (demo mode)"
        }
    }


@app.get("/health", response_model=schemas.HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Use text() for raw SQL
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    redis_status = "healthy" if redis_client.is_available() else "unavailable"
    overall_status = "healthy" if db_status == "healthy" else "degraded"
    
    return schemas.HealthResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        timestamp=datetime.utcnow()
    )


@app.post("/api/v1/cases/search", response_model=schemas.CaseSearchResponse)
async def search_case(
    request: schemas.CaseSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Search for case details by case type, number, and year"""
    try:
        # Check if we already have this query in database
        existing_query = crud.crud_query.get_query_by_case_details(
            db, request.case_type, request.case_number, request.year
        )
        
        if existing_query and existing_query.status == "completed":
            # Return existing data if recent (less than 24 hours old)
            hours_diff = (datetime.utcnow() - existing_query.updated_at).total_seconds() / 3600
            if hours_diff < 24:
                return schemas.CaseSearchResponse(
                    success=True,
                    message="Case details retrieved from database",
                    query=existing_query,
                    cached=True
                )
        
        # Create new query record
        if not existing_query:
            query_record = crud.crud_query.create_query(
                db, request.case_type, request.case_number, request.year
            )
        else:
            query_record = existing_query
            crud.crud_query.update_query_status(db, query_record.id, "pending")
        
        # Perform scraping
        case_data, execution_time = await scraper.search_case_comprehensive(
            request.case_type, request.case_number, request.year
        )
        
        # Log scraping attempt
        log_data = {
            'scraping_type': 'CASE_SEARCH',
            'target_url': 'MULTIPLE_PORTALS',
            'status': 'SUCCESS' if case_data.get('found') else 'FAILED',
            'case_type': request.case_type,
            'case_number': request.case_number,
            'case_year': request.year,
            'records_found': 1 if case_data.get('found') else 0,
            'execution_time': execution_time,
            'error_message': case_data.get('error') if not case_data.get('found') else None
        }
        crud.crud_scraping_log.create_log(db, log_data)
        
        if case_data.get('found'):
            # Create or update case record
            existing_case = crud.crud_case.get_case_by_query(db, query_record.id)
            
            if existing_case:
                crud.crud_case.update_case(db, existing_case.id, case_data)
                case_record = existing_case
            else:
                case_record = crud.crud_case.create_case(db, query_record.id, case_data)
            
            # Create judgment records
            for judgment_info in case_data.get('judgments', []):
                judgment_data = {
                    'judgment_date': judgment_info.get('date'),
                    'judgment_type': judgment_info.get('type', 'ORDER'),
                    'pdf_url': judgment_info.get('url'),
                    'file_name': judgment_info.get('text')
                }
                crud.crud_judgment.create_judgment(db, case_record.id, judgment_data)
            
            # Update query status
            crud.crud_query.update_query_status(db, query_record.id, "completed")
            
            # Refresh query to get updated data
            db.refresh(query_record)
            
            return schemas.CaseSearchResponse(
                success=True,
                message="Case details found and saved",
                query=query_record,
                cached=case_data.get('cached', False),
                execution_time_ms=execution_time
            )
        else:
            # Update query status to failed
            crud.crud_query.update_query_status(db, query_record.id, "failed")
            
            return schemas.CaseSearchResponse(
                success=False,
                message="Case not found in any portal",
                query=query_record,
                execution_time_ms=execution_time
            )
    
    except Exception as e:
        logger.error(f"Case search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while searching for case"
        )


@app.get("/api/v1/cases/recent", response_model=List[schemas.QueryResponse])
async def get_recent_searches(limit: int = 20, db: Session = Depends(get_db)):
    """Get recent case searches"""
    try:
        recent_queries = crud.crud_query.get_recent_queries(db, limit)
        return recent_queries
    except Exception as e:
        logger.error(f"Error fetching recent searches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching recent searches"
        )


@app.post("/api/v1/cause-lists/by-date")
async def get_cause_list_by_date(request: schemas.CauseListRequest, db: Session = Depends(get_db)):
    """Get cause list for a specific date"""
    try:
        # Scrape fresh data
        cause_list_data, execution_time = await scraper.scrape_cause_list_comprehensive(
            request.hearing_date, request.court_name
        )
        
        # Log scraping attempt
        log_data = {
            'scraping_type': 'CAUSE_LIST',
            'target_url': 'MULTIPLE_PORTALS',
            'status': 'SUCCESS' if cause_list_data else 'FAILED',
            'hearing_date': request.hearing_date,
            'records_found': len(cause_list_data),
            'execution_time': execution_time
        }
        crud.crud_scraping_log.create_log(db, log_data)
        
        if cause_list_data:
            # Get court-wise statistics
            court_stats = {}
            for entry in cause_list_data:
                court_name = entry.get('court_name', 'Unknown')
                court_stats[court_name] = court_stats.get(court_name, 0) + 1
            
            return {
                "hearing_date": request.hearing_date,
                "total_cases": len(cause_list_data),
                "court_wise_count": court_stats,
                "entries": cause_list_data,
                "cached": False,
                "last_updated": datetime.utcnow()
            }
        else:
            return {
                "hearing_date": request.hearing_date,
                "total_cases": 0,
                "court_wise_count": {},
                "entries": [],
                "cached": False,
                "last_updated": datetime.utcnow()
            }
    
    except Exception as e:
        logger.error(f"Cause list error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching cause list"
        )


@app.get("/api/v1/cause-lists/courts")
async def get_available_courts(db: Session = Depends(get_db)):
    """Get list of available courts"""
    courts = [
        "Delhi High Court",
        "Supreme Court of India",
        "Bombay High Court",
        "Madras High Court",
        "Calcutta High Court",
        "Karnataka High Court",
        "Allahabad High Court",
        "Rajasthan High Court",
        "Gujarat High Court",
        "Punjab and Haryana High Court"
    ]
    return {"courts": courts}


# NEW REAL SCRAPING ENDPOINTS ADDED BELOW

@app.post("/api/v1/cases/search-real")
async def search_case_real(
    request: schemas.CaseSearchRequest,
    db: Session = Depends(get_db)
):
    """Search for REAL case details from actual eCourts portals"""
    try:
        logger.info(f"REAL case search request: {request.case_type} {request.case_number}/{request.year}")
        
        # Create query record
        db_query = crud.crud_query.create_query(
            db, request.case_type, request.case_number, request.year
        )
        
        # Perform REAL scraping
        case_data, execution_time = await scraper.search_case_comprehensive(
            request.case_type, request.case_number, request.year
        )
        
        # Log the attempt
        log_data = {
            'scraping_type': 'REAL_CASE_SEARCH',
            'target_url': 'MULTIPLE_REAL_PORTALS',
            'status': 'SUCCESS' if case_data.get('found') else 'ATTEMPTED',
            'case_type': request.case_type,
            'case_number': request.case_number,
            'case_year': request.year,
            'records_found': 1 if case_data.get('found') else 0,
            'execution_time': execution_time,
            'error_message': case_data.get('error') if case_data.get('error') else None
        }
        crud.crud_scraping_log.create_log(db, log_data)
        
        # Update query status
        status = "completed" if case_data.get('found') else "attempted"
        crud.crud_query.update_query_status(db, db_query.id, status)
        
        return {
            "success": True,
            "message": "Real scraping attempted - see raw data for details",
            "query": db_query,
            "case_data": case_data,
            "execution_time_ms": execution_time,
            "note": "This shows real portal interaction - actual case data requires form submissions"
        }
        
    except Exception as e:
        logger.error(f"Real case search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Real scraping error: {str(e)}"
        )


@app.get("/api/v1/courts/real")
async def get_real_courts():
    """Get actual courts from eCourts portal"""
    try:
        courts = await scraper.get_available_courts_real()
        return {"courts": courts, "source": "real_ecourts_portals"}
    except Exception as e:
        logger.error(f"Error fetching real courts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching real courts data"
        )


@app.post("/api/v1/cause-lists/real")
async def get_real_cause_list(request: schemas.CauseListRequest, db: Session = Depends(get_db)):
    """Get REAL cause list from actual court portals"""
    try:
        logger.info(f"REAL cause list request for {request.hearing_date}")
        
        # Perform REAL cause list scraping
        cause_list_data, execution_time = await scraper.scrape_cause_list_comprehensive(
            request.hearing_date, request.court_name
        )
        
        # Log the attempt
        log_data = {
            'scraping_type': 'REAL_CAUSE_LIST',
            'target_url': 'REAL_COURT_PORTALS',
            'status': 'SUCCESS' if cause_list_data else 'ATTEMPTED',
            'hearing_date': request.hearing_date,
            'records_found': len(cause_list_data) if cause_list_data else 0,
            'execution_time': execution_time
        }
        crud.crud_scraping_log.create_log(db, log_data)
        
        if cause_list_data:
            # Get court-wise statistics
            court_stats = {}
            for entry in cause_list_data:
                court_name = entry.get('court_name', 'Unknown')
                court_stats[court_name] = court_stats.get(court_name, 0) + 1
            
            return {
                "hearing_date": request.hearing_date,
                "total_cases": len(cause_list_data),
                "court_wise_count": court_stats,
                "entries": cause_list_data,
                "cached": False,
                "last_updated": datetime.utcnow(),
                "source": "real_court_portals",
                "execution_time_ms": execution_time
            }
        else:
            return {
                "hearing_date": request.hearing_date,
                "total_cases": 0,
                "court_wise_count": {},
                "entries": [],
                "cached": False,
                "last_updated": datetime.utcnow(),
                "source": "real_court_portals",
                "message": "No real data found or portal access limited",
                "execution_time_ms": execution_time
            }
        
    except Exception as e:
        logger.error(f"Real cause list error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Real cause list scraping error: {str(e)}"
        )

@app.get("/api/v1/judgments/download/{judgment_id}")
async def download_judgment(judgment_id: int, db: Session = Depends(get_db)):
    """Download judgment document as PDF"""
    try:
        # Get judgment from database
        judgment = db.query(models.Judgment).filter(models.Judgment.id == judgment_id).first()
        
        if not judgment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Judgment not found"
            )
        
        # Get related case and query
        case = judgment.case
        query = case.query if case else None
        
        if not case or not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Related case data not found"
            )
        
        logger.info(f"Generating PDF for judgment {judgment_id}")
        
        # Generate PDF
        pdf_bytes = pdf_generator.generate_judgment_pdf(judgment, case, query)
        
        # Create filename
        filename = f"{query.case_type}_{query.case_number}_{query.year}_judgment_{judgment_id}.pdf"
        
        # Return PDF as downloadable response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Judgment download error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating PDF"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
