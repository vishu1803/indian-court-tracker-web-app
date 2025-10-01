# backend/app/routers/cases.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from app.database import get_db
from app import schemas, crud
from app.scraper import scraper
from app.redis_client import redis_client

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/search", response_model=schemas.CaseSearchResponse)
async def search_case(
    request: schemas.CaseSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Search for case details by case type, number, and year
    """
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

@router.get("/recent", response_model=List[schemas.QueryResponse])
async def get_recent_searches(
    limit: int = 20,
    db: Session = Depends(get_db)
):
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

@router.get("/{query_id}", response_model=schemas.QueryResponse)
async def get_case_by_query_id(
    query_id: int,
    db: Session = Depends(get_db)
):
    """Get case details by query ID"""
    try:
        query = crud.crud_query.get_query(db, query_id)
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query not found"
            )
        return query
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching case details"
        )

@router.post("/{query_id}/refresh")
async def refresh_case_data(
    query_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Refresh case data by re-scraping"""
    try:
        query = crud.crud_query.get_query(db, query_id)
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query not found"
            )
        
        # Invalidate cache
        redis_client.invalidate_case_cache(query.case_type, query.case_number, query.year)
        
        # Add refresh task to background
        background_tasks.add_task(
            _refresh_case_background,
            db, query.id, query.case_type, query.case_number, query.year
        )
        
        return {"message": "Case refresh initiated", "query_id": query_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error initiating case refresh"
        )

async def _refresh_case_background(db: Session, query_id: int, case_type: str, case_number: str, year: int):
    """Background task to refresh case data"""
    try:
        # Update status to pending
        crud.crud_query.update_query_status(db, query_id, "pending")
        
        # Scrape fresh data
        case_data, execution_time = await scraper.search_case_comprehensive(case_type, case_number, year)
        
        if case_data.get('found'):
            # Update case record
            existing_case = crud.crud_case.get_case_by_query(db, query_id)
            if existing_case:
                crud.crud_case.update_case(db, existing_case.id, case_data)
            
            crud.crud_query.update_query_status(db, query_id, "completed")
        else:
            crud.crud_query.update_query_status(db, query_id, "failed")
            
    except Exception as e:
        logger.error(f"Background refresh error: {e}")
        crud.crud_query.update_query_status(db, query_id, "failed")
