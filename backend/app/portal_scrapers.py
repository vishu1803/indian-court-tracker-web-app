from typing import Dict, Optional
from bs4 import BeautifulSoup
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class PortalScraper:
    """Base class for portal-specific scrapers"""
    
    @staticmethod
    def extract_table_data(table: BeautifulSoup) -> Dict[str, str]:
        """Extract data from an HTML table"""
        data = {}
        if not table:
            return data
            
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all(['td', 'th'])
            if len(cols) >= 2:
                key = cols[0].get_text(strip=True).lower()
                value = cols[1].get_text(strip=True)
                key = re.sub(r'[^a-z0-9\s]', '', key).replace(' ', '_')
                if key and value:
                    data[key] = value
        return data

class DelhiHCPortalScraper(PortalScraper):
    """Delhi High Court portal scraper"""
    
    @classmethod
    def extract_case_details(cls, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract case details from Delhi HC portal"""
        try:
            # Find main content
            content = soup.find('div', {'class': re.compile(r'case.*content|main.*content')})
            if not content:
                return None
            
            # Extract case status
            status_elem = content.find(['div', 'span'], string=re.compile(r'status', re.I))
            status = status_elem.find_next(['div', 'span']).get_text(strip=True) if status_elem else None
            
            # Extract case details table
            details_table = content.find('table', {'class': re.compile(r'case.*details|details.*table')})
            details = cls.extract_table_data(details_table)
            
            # Extract parties
            parties = {
                'petitioner': None,
                'respondent': None
            }
            party_section = content.find(['div', 'section'], {'class': re.compile(r'part.*detail')})
            if party_section:
                pet_elem = party_section.find(string=re.compile(r'petition', re.I))
                res_elem = party_section.find(string=re.compile(r'respond', re.I))
                if pet_elem:
                    parties['petitioner'] = pet_elem.find_next(['div', 'span']).get_text(strip=True)
                if res_elem:
                    parties['respondent'] = res_elem.find_next(['div', 'span']).get_text(strip=True)
            
            return {
                'court': 'Delhi High Court',
                'status': status,
                'details': details,
                'parties': parties,
                'last_updated': datetime.now().isoformat(),
                'source': 'delhi_hc_real'
            }
            
        except Exception as e:
            logger.error(f"Delhi HC extraction error: {str(e)}")
            return None

# Add more portal-specific scrapers here
