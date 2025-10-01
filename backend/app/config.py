# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./court_tracker.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "your-super-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Scraping settings
    scraping_delay: int = 2
    max_retries: int = 3
    cache_ttl_hours: int = 24
    cause_list_cache_hours: int = 6
    
    # Court URLs
    high_court_base_url: str = "https://hcservices.ecourts.gov.in/hcservices/main.php"
    district_court_base_url: str = "https://services.ecourts.gov.in/ecourtindia_v6/"
    
    class Config:
        env_file = ".env"

# Create global settings instance
settings = Settings()
