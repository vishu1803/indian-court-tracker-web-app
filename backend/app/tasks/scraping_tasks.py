# backend/app/tasks/scraping_tasks.py
from celery import current_task
from datetime import date, datetime, timedelta
import logging
from typing import List, Dict
import asyncio

from app.tasks import celery_app
from app.database import SessionLocal, get_db
from app.scraper import scraper
from app import crud
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()

@celery_app.task(bind=True, name='app.tasks.scraping_tasks.update_daily_cause_lists')
def update_daily_cause_lists(self):
    """
    Daily task to update cause lists for today and next few days
    """
    try:
        current_task.update_state(state='PROGRESS', meta={'status': 'Starting daily cause list update'})
        
        db = get_db_session()
        dates_to_scrape = []
        
        # Scrape for today and next 3 days
        for i in range(4):
            target_date = date.today() + timedelta(days=i)
            dates_to_scrape.append(target_date)
        
        total_dates = len(dates_to_scrape)
        scraped_entries = 0
        
        for idx, target_date in enumerate(dates_to_scrape):
            try:
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Scraping cause list for {target_date}',
                        'current': idx + 1,
                        'total': total_dates
                    }
                )
                
                # Use asyncio to run async scraper
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                cause_list_data, execution_time = loop.run_until_complete(
                    scraper.scrape_cause_list_comprehensive(target_date)
                )
                
                loop.close()
                
                if cause_list_data:
                    # Save to database
                    crud.crud_cause_list.create_cause_list_entries(db, cause_list_data)
                    scraped_entries += len(cause_list_data)
                    
                    # Log successful scraping
                    log_data = {
                        'scraping_type': 'CAUSE_LIST',
                        'target_url': 'MULTIPLE_PORTALS',
                        'status': 'SUCCESS',
                        'hearing_date': target_date,
                        'records_found': len(cause_list_data),
                        'execution_time': execution_time
                    }
                    crud.crud_scraping_log.create_log(db, log_data)
                    
                    logger.info(f"Scraped {len(cause_list_data)} entries for {target_date}")
                else:
                    # Log failed scraping
                    log_data = {
                        'scraping_type': 'CAUSE_LIST',
                        'target_url': 'MULTIPLE_PORTALS',
                        'status': 'FAILED',
                        'hearing_date': target_date,
                        'records_found': 0,
                        'execution_time': execution_time,
                        'error_message': 'No data found'
                    }
                    crud.crud_scraping_log.create_log(db, log_data)
                
                # Small delay between dates
                import time
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping cause list for {target_date}: {e}")
                
                # Log error
                log_data = {
                    'scraping_type': 'CAUSE_LIST',
                    'target_url': 'MULTIPLE_PORTALS',
                    'status': 'FAILED',
                    'hearing_date': target_date,
                    'records_found': 0,
                    'error_message': str(e)
                }
                crud.crud_scraping_log.create_log(db, log_data)
        
        db.close()
        
        result = {
            'status': 'completed',
            'dates_processed': len(dates_to_scrape),
            'total_entries_scraped': scraped_entries,
            'completion_time': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Daily cause list update completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Daily cause list update failed: {e}", exc_info=True)
        raise self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes

@celery_app.task(bind=True, name='app.tasks.scraping_tasks.cleanup_old_data')
def cleanup_old_data(self):
    """
    Weekly task to clean up old data and optimize database
    """
    try:
        current_task.update_state(state='PROGRESS', meta={'status': 'Starting data cleanup'})
        
        db = get_db_session()
        
        # Delete cause list entries older than 30 days
        cutoff_date = date.today() - timedelta(days=30)
        
        old_cause_lists = db.query(crud.models.CauseList).filter(
            crud.models.CauseList.hearing_date < cutoff_date
        )
        deleted_cause_lists = old_cause_lists.count()
        old_cause_lists.delete()
        
        # Delete scraping logs older than 90 days
        log_cutoff_date = datetime.utcnow() - timedelta(days=90)
        old_logs = db.query(crud.models.ScrapingLog).filter(
            crud.models.ScrapingLog.created_at < log_cutoff_date
        )
        deleted_logs = old_logs.count()
        old_logs.delete()
        
        # Delete failed queries older than 7 days
        query_cutoff_date = datetime.utcnow() - timedelta(days=7)
        failed_queries = db.query(crud.models.Query).filter(
            crud.models.Query.status == 'failed',
            crud.models.Query.created_at < query_cutoff_date
        )
        deleted_queries = failed_queries.count()
        failed_queries.delete()
        
        db.commit()
        db.close()
        
        # Clear old Redis cache
        if redis_client.is_available():
            # This would clear all cache - use with caution in production
            # redis_client.clear_all_cache()
            pass
        
        result = {
            'status': 'completed',
            'deleted_cause_lists': deleted_cause_lists,
            'deleted_logs': deleted_logs,
            'deleted_failed_queries': deleted_queries,
            'completion_time': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Data cleanup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}", exc_info=True)
        raise self.retry(countdown=600, max_retries=2)  # Retry after 10 minutes

@celery_app.task(bind=True, name='app.tasks.scraping_tasks.update_daily_statistics')
def update_daily_statistics(self):
    """
    Daily task to update statistics and cache performance metrics
    """
    try:
        current_task.update_state(state='PROGRESS', meta={'status': 'Calculating daily statistics'})
        
        db = get_db_session()
        
        # Get today's statistics
        daily_stats = crud.crud_scraping_log.get_daily_stats(db)
        
        # Get Redis cache statistics
        redis_stats = redis_client.get_cache_stats()
        
        # Calculate cache hit rate
        total_requests = daily_stats.get('total_queries', 0)
        cache_hits = redis_stats.get('hits', 0)
        cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        # Store statistics in Redis for quick access
        stats_data = {
            'date': date.today().isoformat(),
            'scraping_stats': daily_stats,
            'redis_stats': redis_stats,
            'cache_hit_rate': cache_hit_rate,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if redis_client.is_available():
            redis_client.redis_client.setex(
                'daily_stats',
                86400,  # 24 hours
                str(stats_data)
            )
        
        db.close()
        
        logger.info(f"Daily statistics updated: {stats_data}")
        return stats_data
        
    except Exception as e:
        logger.error(f"Statistics update failed: {e}", exc_info=True)
        raise self.retry(countdown=300, max_retries=2)

@celery_app.task(bind=True, name='app.tasks.scraping_tasks.refresh_case_data_batch')
def refresh_case_data_batch(self, case_ids: List[int]):
    """
    Background task to refresh multiple cases
    """
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={'status': f'Refreshing {len(case_ids)} cases'}
        )
        
        db = get_db_session()
        refreshed_count = 0
        
        for idx, case_id in enumerate(case_ids):
            try:
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Refreshing case {case_id}',
                        'current': idx + 1,
                        'total': len(case_ids)
                    }
                )
                
                query = crud.crud_query.get_query(db, case_id)
                if query:
                    # Clear cache
                    redis_client.invalidate_case_cache(
                        query.case_type, query.case_number, query.year
                    )
                    
                    # Scrape fresh data
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    case_data, execution_time = loop.run_until_complete(
                        scraper.search_case_comprehensive(
                            query.case_type, query.case_number, query.year
                        )
                    )
                    
                    loop.close()
                    
                    if case_data.get('found'):
                        # Update case record
                        existing_case = crud.crud_case.get_case_by_query(db, case_id)
                        if existing_case:
                            crud.crud_case.update_case(db, existing_case.id, case_data)
                        
                        crud.crud_query.update_query_status(db, case_id, "completed")
                        refreshed_count += 1
                    else:
                        crud.crud_query.update_query_status(db, case_id, "failed")
                
                # Small delay between cases
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error refreshing case {case_id}: {e}")
                crud.crud_query.update_query_status(db, case_id, "failed")
        
        db.close()
        
        result = {
            'status': 'completed',
            'total_cases': len(case_ids),
            'refreshed_count': refreshed_count,
            'completion_time': datetime.utcnow().isoformat()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Batch refresh failed: {e}", exc_info=True)
        raise self.retry(countdown=300, max_retries=2)
