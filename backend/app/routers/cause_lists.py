# backend/app/routers/cause_lists.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
import logging

from app.database import get_db
from app import schemas, crud
from app.scraper import scraper
from app.redis_client import redis_client

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/by-date", response_model=schemas.CauseListResponse)
async def get_cause_list_by_date(
    request: schemas.CauseListRequest,
    db: Session = Depends(get_db)
):
    """
    Get cause list for a specific date
    """
    try:
        # Check if we have recent data in database
        existing_entries = crud.crud_cause_list.get_cause_list_by_date(
            db, request.hearing_date, request.court_name
        )
        
        # If we have recent data (less than 6 hours old), return it
        if existing_entries:
            latest_entry = max(existing_entries, key=lambda x: x.scraped_at)
            hours_diff = (datetime.utcnow() - latest_entry.scraped_at).total_seconds() / 3600
            
            if hours_diff < 6:  # Use cached data if less than 6 hours old
                court_stats = crud.crud_cause_list.get_court_wise_stats(db, request.hearing_date)
                
                return schemas.CauseListResponse(
                    hearing_date=request.hearing_date,
                    total_cases=len(existing_entries),
                    court_wise_count=court_stats,
                    entries=existing_entries,
                    cached=True,
                    last_updated=latest_entry.scraped_at
                )
        
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
            # Save to database
            crud.crud_cause_list.create_cause_list_entries(db, cause_list_data)
            
            # Get court-wise statistics
            court_stats = {}
            for entry in cause_list_data:
                court_name = entry.get('court_name', 'Unknown')
                court_stats[court_name] = court_stats.get(court_name, 0) + 1
            
            return schemas.CauseListResponse(
                hearing_date=request.hearing_date,
                total_cases=len(cause_list_data),
                court_wise_count=court_stats,
                entries=[schemas.CauseListEntry(**entry) for entry in cause_list_data],
                cached=False,
                last_updated=datetime.utcnow()
            )
        else:
            return schemas.CauseListResponse(
                hearing_date=request.hearing_date,
                total_cases=0,
                court_wise_count={},
                entries=[],
                cached=False,
                last_updated=datetime.utcnow()
            )
    
    except Exception as e:
        logger.error(f"Cause list error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching cause list"
        )

@router.get("/check-case")
async def check_case_in_cause_list(
    case_type: str = Query(..., description="Case type"),
    case_number: str = Query(..., description="Case number"),
    year: int = Query(..., description="Case year"),
    hearing_date: date = Query(..., description="Hearing date to check"),
    db: Session = Depends(get_db)
):
    """
    Check if a specific case is listed in cause list for a given date
    """
    try:
        # Check in database first
        listings = crud.crud_cause_list.check_case_in_cause_list(
            db, case_number, case_type, year, hearing_date
        )
        
        if listings:
            return {
                "found": True,
                "hearing_date": hearing_date,
                "case_details": {
                    "case_type": case_type,
                    "case_number": case_number,
                    "year": year
                },
                "listings": [
                    {
                        "court_name": listing.court_name,
                        "hearing_time": listing.hearing_time,
                        "court_hall": listing.court_hall,
                        "judge_name": listing.judge_name,
                        "parties": listing.parties
                    }
                    for listing in listings
                ]
            }
        else:
            # If not found in database, try fresh scraping
            cause_list_data, _ = await scraper.scrape_cause_list_comprehensive(hearing_date)
            
            # Check in scraped data
            matching_entries = [
                entry for entry in cause_list_data
                if (entry.get('case_number') == case_number and 
                    entry.get('case_type', '').upper() == case_type.upper() and
                    entry.get('case_year') == year)
            ]
            
            if matching_entries:
                # Save to database for future queries
                crud.crud_cause_list.create_cause_list_entries(db, cause_list_data)
                
                return {
                    "found": True,
                    "hearing_date": hearing_date,
                    "case_details": {
                        "case_type": case_type,
                        "case_number": case_number,
                        "year": year
                    },
                    "listings": [
                        {
                            "court_name": entry.get('court_name'),
                            "hearing_time": entry.get('hearing_time'),
                            "court_hall": entry.get('court_hall'),
                            "judge_name": entry.get('judge_name'),
                            "parties": entry.get('parties')
                        }
                        for entry in matching_entries
                    ]
                }
        
        return {
            "found": False,
            "hearing_date": hearing_date,
            "case_details": {
                "case_type": case_type,
                "case_number": case_number,
                "year": year
            },
            "message": "Case not found in cause list for the specified date"
        }
    
    except Exception as e:
        logger.error(f"Check case listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking case in cause list"
        )

@router.get("/courts")
async def get_available_courts(
    db: Session = Depends(get_db)
):
    """Get list of available courts from cause list data"""
    try:
        # Get distinct court names from cause list table
        court_names = db.query(
            crud.models.CauseList.court_name
        ).distinct().order_by(crud.models.CauseList.court_name).all()
        
        return {
            "courts": [court[0] for court in court_names if court[0]]
        }
    
    except Exception as e:
        logger.error(f"Error fetching courts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching available courts"
        )

@router.get("/stats")
async def get_cause_list_stats(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get cause list statistics"""
    try:
        # Set default date range if not provided
        if not date_from:
            date_from = date.today()
        if not date_to:
            date_to = date.today()
        
        # Get statistics from database
        query = db.query(crud.models.CauseList).filter(
            crud.models.CauseList.hearing_date.between(date_from, date_to)
        )
        
        total_cases = query.count()
        
        # Court-wise breakdown
        court_stats = {}
        court_results = query.with_entities(
            crud.models.CauseList.court_name,
            crud.func.count(crud.models.CauseList.id)
        ).group_by(crud.models.CauseList.court_name).all()
        
        for court, count in court_results:
            court_stats[court] = count
        
        # Case type breakdown
        case_type_stats = {}
        type_results = query.with_entities(
            crud.models.CauseList.case_type,
            crud.func.count(crud.models.CauseList.id)
        ).group_by(crud.models.CauseList.case_type).all()
        
        for case_type, count in type_results:
            case_type_stats[case_type] = count
        
        return {
            "date_range": {
                "from": date_from,
                "to": date_to
            },
            "total_cases": total_cases,
            "court_wise_breakdown": court_stats,
            "case_type_breakdown": case_type_stats
        }
    
    except Exception as e:
        logger.error(f"Error fetching cause list stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching cause list statistics"
        )
