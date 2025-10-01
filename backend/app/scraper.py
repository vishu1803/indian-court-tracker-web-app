# backend/app/scraper.py
import asyncio
import time
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
import re

from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup, Tag
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import settings
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

class CourtsDataScraper:
    """Comprehensive scraper for Indian eCourts portals"""
    
    def __init__(self):
        self.high_court_url = settings.high_court_base_url
        self.district_court_url = settings.district_court_base_url
        self.scraping_delay = settings.scraping_delay
        self.max_retries = settings.max_retries
        
        # Setup HTTP session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    async def search_case_comprehensive(self, case_type: str, case_number: str, year: int) -> Tuple[Dict[str, Any], int]:
        """
        Comprehensive case search across both portals
        Returns: (case_data, execution_time_ms)
        """
        start_time = time.time()
        
        # Check Redis cache first
        cached_data = redis_client.get_case_data(case_type, case_number, year)
        if cached_data:
            execution_time = int((time.time() - start_time) * 1000)
            cached_data['cached'] = True
            return cached_data, execution_time
        
        case_data = {
            'case_type': case_type.upper(),
            'case_number': case_number,
            'year': year,
            'found': False,
            'cached': False,
            'data_source': None,
            'search_attempts': []
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            try:
                # Try High Court first
                hc_result = await self._search_high_court(browser, case_type, case_number, year)
                case_data['search_attempts'].append({
                    'portal': 'HIGH_COURT',
                    'success': hc_result is not None,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                if hc_result:
                    case_data.update(hc_result)
                    case_data['found'] = True
                    case_data['data_source'] = 'HIGH_COURT_PORTAL'
                else:
                    # Try District Court
                    await asyncio.sleep(self.scraping_delay)  # Rate limiting
                    dc_result = await self._search_district_court(browser, case_type, case_number, year)
                    case_data['search_attempts'].append({
                        'portal': 'DISTRICT_COURT',
                        'success': dc_result is not None,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    if dc_result:
                        case_data.update(dc_result)
                        case_data['found'] = True
                        case_data['data_source'] = 'DISTRICT_COURT_PORTAL'
                
            except Exception as e:
                logger.error(f"Case search error for {case_type} {case_number}/{year}: {e}")
                case_data['error'] = str(e)
            finally:
                await browser.close()
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Cache successful results
        if case_data['found']:
            redis_client.set_case_data(case_type, case_number, year, case_data)
        
        return case_data, execution_time
    
    async def _search_high_court(self, browser: Browser, case_type: str, case_number: str, year: int) -> Optional[Dict]:
        """Search High Court portal"""
        try:
            page = await browser.new_page()
            
            # Set user agent to avoid blocking
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            logger.info(f"Searching High Court: {case_type} {case_number}/{year}")
            
            # Navigate to High Court portal
            await page.goto(self.high_court_url, wait_until='networkidle')
            
            # Look for case status link
            case_status_selector = 'a[href*="case"], a[href*="status"], text="Case Status"'
            try:
                await page.wait_for_selector(case_status_selector, timeout=10000)
                await page.click(case_status_selector)
                await page.wait_for_load_state('networkidle')
            except:
                # Try alternative navigation
                await page.goto(f"{self.high_court_url}?p=case_status", wait_until='networkidle')
            
            # Fill search form
            await self._fill_case_search_form(page, case_type, case_number, year)
            
            # Submit and wait for results
            await page.click('input[type="submit"], button[type="submit"], input[value*="Search"]')
            await page.wait_for_load_state('networkidle')
            
            # Parse results
            content = await page.content()
            case_data = await self._parse_case_details(content, 'HIGH_COURT')
            
            await page.close()
            return case_data if case_data.get('parties_petitioner') or case_data.get('case_status') else None
            
        except Exception as e:
            logger.error(f"High Court search error: {e}")
            return None
    
    async def _search_district_court(self, browser: Browser, case_type: str, case_number: str, year: int) -> Optional[Dict]:
        """Search District Court portal"""
        try:
            page = await browser.new_page()
            
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            logger.info(f"Searching District Court: {case_type} {case_number}/{year}")
            
            # Navigate to District Court portal
            await page.goto(self.district_court_url, wait_until='networkidle')
            
            # Navigate to case status
            case_status_link = 'a[href*="casestatus"], text="Case Status"'
            try:
                await page.wait_for_selector(case_status_link, timeout=10000)
                await page.click(case_status_link)
                await page.wait_for_load_state('networkidle')
            except:
                await page.goto(f"{self.district_court_url}?p=casestatus/index", wait_until='networkidle')
            
            # Select "By Case Number" option if available
            try:
                by_case_number = 'a[href*="case_no"], text="By Case Number", text="Case Number"'
                await page.wait_for_selector(by_case_number, timeout=5000)
                await page.click(by_case_number)
                await page.wait_for_load_state('networkidle')
            except:
                pass  # Continue with current page
            
            # Fill search form
            await self._fill_case_search_form(page, case_type, case_number, year)
            
            # Submit search
            await page.click('input[value="Search"], input[type="submit"], button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Parse results
            content = await page.content()
            case_data = await self._parse_case_details(content, 'DISTRICT_COURT')
            
            await page.close()
            return case_data if case_data.get('parties_petitioner') or case_data.get('case_status') else None
            
        except Exception as e:
            logger.error(f"District Court search error: {e}")
            return None
    
    async def _fill_case_search_form(self, page: Page, case_type: str, case_number: str, year: int):
        """Fill case search form with intelligent field detection"""
        try:
            # Try different case type field selectors
            case_type_selectors = [
                'select[name="case_type"]',
                'select[name="casetype"]',
                'select[name="ctype"]',
                'select[id*="case_type"]',
                'select[id*="casetype"]'
            ]
            
            for selector in case_type_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    # Try to select by value or text
                    try:
                        await page.select_option(selector, value=case_type.upper())
                    except:
                        await page.select_option(selector, label=case_type.upper())
                    break
                except:
                    continue
            
            # Try different case number field selectors
            case_number_selectors = [
                'input[name="case_no"]',
                'input[name="caseno"]',
                'input[name="case_number"]',
                'input[id*="case_no"]',
                'input[id*="caseno"]'
            ]
            
            for selector in case_number_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    await page.fill(selector, case_number)
                    break
                except:
                    continue
            
            # Try different year field selectors
            year_selectors = [
                'select[name="case_year"]',
                'select[name="year"]',
                'select[name="caseyear"]',
                'input[name="case_year"]',
                'input[name="year"]'
            ]
            
            for selector in year_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    if selector.startswith('select'):
                        await page.select_option(selector, str(year))
                    else:
                        await page.fill(selector, str(year))
                    break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Form filling warning: {e}")
    
    async def _parse_case_details(self, html_content: str, court_type: str) -> Dict[str, Any]:
        """Parse case details from HTML with intelligent extraction"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        case_data = {
            'court_type': court_type,
            'parties_petitioner': None,
            'parties_respondent': None,
            'filing_date': None,
            'registration_date': None,
            'next_hearing_date': None,
            'case_status': None,
            'court_name': None,
            'judge_name': None,
            'court_hall': None,
            'case_category': None,
            'disposal_nature': None,
            'judgments': []
        }
        
        # Look for case information in various table structures
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    field_name = cells[0].get_text().strip().lower()
                    field_value = cells[1].get_text().strip()
                    
                    # Map field names to case data
                    if any(keyword in field_name for keyword in ['petitioner', 'appellant', 'plaintiff']):
                        case_data['parties_petitioner'] = field_value
                    elif any(keyword in field_name for keyword in ['respondent', 'defendant', 'appellee']):
                        case_data['parties_respondent'] = field_value
                    elif any(keyword in field_name for keyword in ['filing', 'filed', 'registration']):
                        case_data['filing_date'] = self._parse_date_string(field_value)
                    elif any(keyword in field_name for keyword in ['next hearing', 'hearing date', 'next date']):
                        case_data['next_hearing_date'] = self._parse_date_string(field_value)
                    elif any(keyword in field_name for keyword in ['status', 'stage']):
                        case_data['case_status'] = field_value
                    elif any(keyword in field_name for keyword in ['court', 'bench']):
                        case_data['court_name'] = field_value
                    elif any(keyword in field_name for keyword in ['judge', 'coram', 'before']):
                        case_data['judge_name'] = field_value
                    elif any(keyword in field_name for keyword in ['hall', 'room', 'court no']):
                        case_data['court_hall'] = field_value
                    elif any(keyword in field_name for keyword in ['category', 'nature', 'type']):
                        case_data['case_category'] = field_value
        
        # Look for judgment/order links
        links = soup.find_all('a', href=True)
        for link in links:
            link_text = link.get_text().strip().lower()
            if any(keyword in link_text for keyword in ['judgment', 'order', 'decree']):
                judgment_info = {
                    'url': link.get('href'),
                    'text': link.get_text().strip(),
                    'type': 'JUDGMENT' if 'judgment' in link_text else 'ORDER'
                }
                
                # Try to extract date from link text
                date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', link.get_text())
                if date_match:
                    judgment_info['date'] = self._parse_date_string(date_match.group(1))
                
                case_data['judgments'].append(judgment_info)
        
        # Clean up empty fields
        for key, value in case_data.items():
            if isinstance(value, str) and (not value or value.lower() in ['n/a', 'na', 'nil', '-', '']):
                case_data[key] = None
        
        return case_data
    
    def _parse_date_string(self, date_str: str) -> Optional[date]:
        """Parse various date formats commonly used in Indian courts"""
        if not date_str or date_str.strip().lower() in ['n/a', 'na', 'nil', '-', '']:
            return None
        
        # Clean the date string
        date_str = date_str.strip()
        
        # Common date formats in Indian courts
        date_formats = [
            '%d/%m/%Y',   # 15/03/2024
            '%d-%m-%Y',   # 15-03-2024
            '%d.%m.%Y',   # 15.03.2024
            '%Y-%m-%d',   # 2024-03-15
            '%d/%m/%y',   # 15/03/24
            '%d-%m-%y',   # 15-03-24
            '%d %b %Y',   # 15 Mar 2024
            '%d %B %Y',   # 15 March 2024
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                # Validate date range (courts started computerization around 1990)
                if 1990 <= parsed_date.year <= 2030:
                    return parsed_date
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    async def scrape_cause_list_comprehensive(self, target_date: date, court_filter: Optional[str] = None) -> Tuple[List[Dict], int]:
        """
        Scrape cause lists from both portals
        Returns: (cause_list_entries, execution_time_ms)
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{target_date}:{court_filter or 'all'}"
        cached_data = redis_client.get_cause_list(str(target_date), court_filter or 'all')
        if cached_data:
            execution_time = int((time.time() - start_time) * 1000)
            return cached_data, execution_time
        
        all_entries = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                # Scrape High Court cause lists
                hc_entries = await self._scrape_high_court_cause_list(browser, target_date)
                all_entries.extend(hc_entries)
                
                # Rate limiting between portals
                await asyncio.sleep(self.scraping_delay)
                
                # Scrape District Court cause lists
                dc_entries = await self._scrape_district_court_cause_list(browser, target_date)
                all_entries.extend(dc_entries)
                
            except Exception as e:
                logger.error(f"Cause list scraping error: {e}")
            finally:
                await browser.close()
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Filter by court if specified
        if court_filter:
            all_entries = [entry for entry in all_entries if court_filter.lower() in entry.get('court_name', '').lower()]
        
        # Cache results
        if all_entries:
            redis_client.set_cause_list(str(target_date), court_filter or 'all', all_entries)
        
        return all_entries, execution_time
    
    async def _scrape_high_court_cause_list(self, browser: Browser, target_date: date) -> List[Dict]:
        """Scrape High Court cause list"""
        try:
            page = await browser.new_page()
            
            logger.info(f"Scraping High Court cause list for {target_date}")
            
            await page.goto(self.high_court_url, wait_until='networkidle')
            
            # Navigate to cause list section
            cause_list_selectors = [
                'a[href*="cause"], a[href*="daily"], text="Cause List", text="Daily List"'
            ]
            
            for selector in cause_list_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.click(selector)
                    await page.wait_for_load_state('networkidle')
                    break
                except:
                    continue
            
            # Fill date field
            date_str = target_date.strftime('%d/%m/%Y')
            date_selectors = [
                'input[name="date"]',
                'input[name="hearing_date"]',
                'input[type="date"]',
                'input[id*="date"]'
            ]
            
            for selector in date_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.fill(selector, date_str)
                    break
                except:
                    continue
            
            # Submit search
            await page.click('input[value*="Search"], input[value*="Get"], button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Parse cause list
            content = await page.content()
            entries = self._parse_cause_list_html(content, 'HIGH_COURT', target_date)
            
            await page.close()
            return entries
            
        except Exception as e:
            logger.error(f"High Court cause list error: {e}")
            return []
    
    async def _scrape_district_court_cause_list(self, browser: Browser, target_date: date) -> List[Dict]:
        """Scrape District Court cause list"""
        try:
            page = await browser.new_page()
            
            logger.info(f"Scraping District Court cause list for {target_date}")
            
            await page.goto(self.district_court_url, wait_until='networkidle')
            
            # Navigate to cause list
            try:
                await page.click('a[href*="cause"], text="Cause List"')
                await page.wait_for_load_state('networkidle')
            except:
                await page.goto(f"{self.district_court_url}?p=cause_list/index", wait_until='networkidle')
            
            # Fill date
            date_str = target_date.strftime('%d/%m/%Y')
            try:
                await page.fill('input[name="date"]', date_str)
            except:
                pass
            
            # Submit
            await page.click('input[value="Search"], input[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Parse results
            content = await page.content()
            entries = self._parse_cause_list_html(content, 'DISTRICT_COURT', target_date)
            
            await page.close()
            return entries
            
        except Exception as e:
            logger.error(f"District Court cause list error: {e}")
            return []
    
    def _parse_cause_list_html(self, html_content: str, court_type: str, hearing_date: date) -> List[Dict]:
        """Parse cause list from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        entries = []
        
        # Find cause list tables
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            # Skip header row
            data_rows = rows[1:] if rows else []
            
            for row in data_rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 3:  # Minimum required columns
                    entry = {
                        'court_type': court_type,
                        'hearing_date': hearing_date,
                        'case_number': cells[0].get_text().strip() if len(cells) > 0 else '',
                        'case_type': cells[1].get_text().strip() if len(cells) > 1 else '',
                        'parties': cells[2].get_text().strip() if len(cells) > 2 else '',
                        'court_hall': cells[3].get_text().strip() if len(cells) > 3 else '',
                        'judge_name': cells[4].get_text().strip() if len(cells) > 4 else '',
                        'hearing_time': cells[5].get_text().strip() if len(cells) > 5 else '',
                        'hearing_purpose': cells[6].get_text().strip() if len(cells) > 6 else '',
                        'data_source': f'{court_type}_PORTAL'
                    }
                    
                    # Extract case year from case number if possible
                    case_number_match = re.search(r'/(\d{4})', entry['case_number'])
                    if case_number_match:
                        entry['case_year'] = int(case_number_match.group(1))
                    
                    # Only add if has meaningful data
                    if entry['case_number'] and entry['parties']:
                        entries.append(entry)
        
        logger.info(f"Parsed {len(entries)} cause list entries from {court_type}")
        return entries

# Create global scraper instance
scraper = CourtsDataScraper()
