# backend/init_database.py
from app.database import init_db
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"Initializing database at: {settings.database_url}")
    try:
        init_db()
        logger.info("✅ Database initialized successfully!")
        logger.info("Tables created: users, queries, cases, judgments, cause_list, scraping_logs")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
