# backend/app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, distinct
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime, timedelta
import logging

from app import models, schemas

logger = logging.getLogger(__name__)

class CRUDQuery:
    """CRUD operations for Query model"""
    
    def create_query(self, db: Session, case_type: str, case_number: str, year: int, user_id: Optional[int] = None) -> models.Query:
        """Create a new search query"""
        db_query = models.Query(
            case_type=case_type.upper(),
            case_number=case_number,
            year=year,
            user_id=user_id,
            status="pending"
        )
        db.add(db_query)
        db.commit()
        db.refresh(db_query)
        logger.info(f"Created query {db_query.id}: {case_type} {case_number}/{year}")
        return db_query
    
    def get_query(self, db: Session, query_id: int) -> Optional[models.Query]:
        """Get query by ID"""
        return db.query(models.Query).filter(models.Query.id == query_id).first()
    
    def get_query_by_case_details(self, db: Session, case_type: str, case_number: str, year: int) -> Optional[models.Query]:
        """Find existing query by case details"""
        return db.query(models.Query).filter(
            and_(
                models.Query.case_type == case_type.upper(),
                models.Query.case_number == case_number,
                models.Query.year == year
            )
        ).first()
    
    def update_query_status(self, db: Session, query_id: int, status: str) -> bool:
        """Update query status"""
        try:
            db.query(models.Query).filter(models.Query.id == query_id).update({
                "status": status,
                "updated_at": datetime.utcnow()
            })
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating query {query_id}: {e}")
            db.rollback()
            return False
    
    def get_recent_queries(self, db: Session, limit: int = 50, user_id: Optional[int] = None) -> List[models.Query]:
        """Get recent queries"""
        query = db.query(models.Query)
        if user_id:
            query = query.filter(models.Query.user_id == user_id)
        return query.order_by(desc(models.Query.created_at)).limit(limit).all()

class CRUDCase:
    """CRUD operations for Case model"""
    
    def create_case(self, db: Session, query_id: int, case_data: Dict[str, Any]) -> models.Case:
        """Create a new case record"""
        db_case = models.Case(
            query_id=query_id,
            parties_petitioner=case_data.get('parties_petitioner'),
            parties_respondent=case_data.get('parties_respondent'),
            filing_date=case_data.get('filing_date'),
            registration_date=case_data.get('registration_date'),
            next_hearing_date=case_data.get('next_hearing_date'),
            case_status=case_data.get('case_status'),
            court_name=case_data.get('court_name'),
            court_type=case_data.get('court_type'),
            judge_name=case_data.get('judge_name'),
            court_hall=case_data.get('court_hall'),
            case_category=case_data.get('case_category'),
            case_subcategory=case_data.get('case_subcategory'),
            disposal_nature=case_data.get('disposal_nature'),
            data_source=case_data.get('data_source'),
            last_updated=datetime.utcnow()
        )
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        logger.info(f"Created case {db_case.id} for query {query_id}")
        return db_case
    
    def get_case_by_query(self, db: Session, query_id: int) -> Optional[models.Case]:
        """Get case by query ID"""
        return db.query(models.Case).filter(models.Case.query_id == query_id).first()
    
    def update_case(self, db: Session, case_id: int, case_data: Dict[str, Any]) -> bool:
        """Update existing case"""
        try:
            case_data['last_updated'] = datetime.utcnow()
            db.query(models.Case).filter(models.Case.id == case_id).update(case_data)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating case {case_id}: {e}")
            db.rollback()
            return False

class CRUDJudgment:
    """CRUD operations for Judgment model"""
    
    def create_judgment(self, db: Session, case_id: int, judgment_data: Dict[str, Any]) -> models.Judgment:
        """Create a new judgment record"""
        db_judgment = models.Judgment(
            case_id=case_id,
            judgment_date=judgment_data.get('judgment_date'),
            judgment_type=judgment_data.get('judgment_type', 'ORDER'),
            pdf_url=judgment_data.get('pdf_url'),
            file_name=judgment_data.get('file_name'),
            file_size=judgment_data.get('file_size'),
            content_text=judgment_data.get('content_text'),
            download_status='pending'
        )
        db.add(db_judgment)
        db.commit()
        db.refresh(db_judgment)
        logger.info(f"Created judgment {db_judgment.id} for case {case_id}")
        return db_judgment
    
    def get_judgments_by_case(self, db: Session, case_id: int) -> List[models.Judgment]:
        """Get all judgments for a case"""
        return db.query(models.Judgment).filter(models.Judgment.case_id == case_id).order_by(desc(models.Judgment.judgment_date)).all()
    
    def update_download_status(self, db: Session, judgment_id: int, status: str, file_size: Optional[int] = None) -> bool:
        """Update judgment download status"""
        try:
            update_data = {"download_status": status, "updated_at": datetime.utcnow()}
            if file_size:
                update_data["file_size"] = file_size
            
            db.query(models.Judgment).filter(models.Judgment.id == judgment_id).update(update_data)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating judgment {judgment_id}: {e}")
            db.rollback()
            return False

class CRUDCauseList:
    """CRUD operations for CauseList model"""
    
    def create_cause_list_entries(self, db: Session, entries: List[Dict[str, Any]]) -> List[models.CauseList]:
        """Create multiple cause list entries"""
        db_entries = []
        for entry_data in entries:
            db_entry = models.CauseList(
                court_name=entry_data.get('court_name'),
                court_type=entry_data.get('court_type'),
                case_number=entry_data.get('case_number'),
                case_type=entry_data.get('case_type'),
                case_year=entry_data.get('case_year'),
                parties=entry_data.get('parties'),
                hearing_date=entry_data.get('hearing_date'),
                hearing_time=entry_data.get('hearing_time'),
                court_hall=entry_data.get('court_hall'),
                judge_name=entry_data.get('judge_name'),
                hearing_purpose=entry_data.get('hearing_purpose'),
                case_status_in_list=entry_data.get('case_status_in_list'),
                data_source=entry_data.get('data_source'),
                scraped_at=datetime.utcnow()
            )
            db_entries.append(db_entry)
        
        db.add_all(db_entries)
        db.commit()
        logger.info(f"Created {len(db_entries)} cause list entries")
        return db_entries
    
    def get_cause_list_by_date(self, db: Session, hearing_date: date, court_name: Optional[str] = None) -> List[models.CauseList]:
        """Get cause list entries by date"""
        query = db.query(models.CauseList).filter(models.CauseList.hearing_date == hearing_date)
        if court_name:
            query = query.filter(models.CauseList.court_name.ilike(f"%{court_name}%"))
        return query.order_by(models.CauseList.court_name, models.CauseList.hearing_time).all()
    
    def check_case_in_cause_list(self, db: Session, case_number: str, case_type: str, year: int, hearing_date: date) -> List[models.CauseList]:
        """Check if a case is listed in cause list for a specific date"""
        return db.query(models.CauseList).filter(
            and_(
                models.CauseList.case_number == case_number,
                models.CauseList.case_type == case_type.upper(),
                models.CauseList.case_year == year,
                models.CauseList.hearing_date == hearing_date
            )
        ).all()
    
    def get_court_wise_stats(self, db: Session, hearing_date: date) -> Dict[str, int]:
        """Get court-wise case count for a date"""
        results = db.query(
            models.CauseList.court_name,
            func.count(models.CauseList.id).label('count')
        ).filter(
            models.CauseList.hearing_date == hearing_date
        ).group_by(models.CauseList.court_name).all()
        
        return {court: count for court, count in results}

class CRUDScrapingLog:
    """CRUD operations for ScrapingLog model"""
    
    def create_log(self, db: Session, log_data: Dict[str, Any]) -> models.ScrapingLog:
        """Create a scraping log entry"""
        db_log = models.ScrapingLog(
            scraping_type=log_data.get('scraping_type'),
            target_url=log_data.get('target_url'),
            status=log_data.get('status'),
            case_type=log_data.get('case_type'),
            case_number=log_data.get('case_number'),
            case_year=log_data.get('case_year'),
            hearing_date=log_data.get('hearing_date'),
            records_found=log_data.get('records_found', 0),
            error_message=log_data.get('error_message'),
            execution_time=log_data.get('execution_time')
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log
    
    def get_daily_stats(self, db: Session, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Get daily scraping statistics"""
        if not target_date:
            target_date = date.today()
        
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        # Get counts by status
        results = db.query(
            models.ScrapingLog.status,
            func.count(models.ScrapingLog.id).label('count'),
            func.avg(models.ScrapingLog.execution_time).label('avg_time')
        ).filter(
            models.ScrapingLog.created_at.between(start_datetime, end_datetime)
        ).group_by(models.ScrapingLog.status).all()
        
        stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'average_response_time_ms': 0.0
        }
        
        total_time = 0
        for status, count, avg_time in results:
            stats['total_queries'] += count
            if status == 'SUCCESS':
                stats['successful_queries'] += count
            elif status == 'FAILED':
                stats['failed_queries'] += count
            
            if avg_time:
                total_time += avg_time * count
        
        if stats['total_queries'] > 0:
            stats['average_response_time_ms'] = total_time / stats['total_queries']
        
        return stats

# Create CRUD instances
crud_query = CRUDQuery()
crud_case = CRUDCase()
crud_judgment = CRUDJudgment()
crud_cause_list = CRUDCauseList()
crud_scraping_log = CRUDScrapingLog()
