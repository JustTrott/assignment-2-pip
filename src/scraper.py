# Main scraping logic
#!/usr/bin/env python3
"""
iloveny.com/events Web Scraper
Implements the scraping strategy with Beautiful Soup, respectful crawling,
and comprehensive error handling.
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import random
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Data structure for event information"""
    title: str = ""
    date_start: str = ""
    date_end: str = ""
    location: str = ""
    category: str = ""
    description: str = ""
    url: str = ""
    image_url: str = ""
    organizer: str = ""
    region: str = ""
    ticket_info: str = ""
    scraped_at: str = ""

class ILoveNYScraper:
    def __init__(self, output_dir: str = "scraped_data", delay_range: tuple = (2, 5)):
        """
        Initialize the scraper with configuration
        
        Args:
            output_dir: Directory to save output files
            delay_range: Min and max seconds to wait between requests
        """
        self.base_url = "https://www.iloveny.com"
        self.events_url = f"{self.base_url}/events"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.delay_range = delay_range
        self.max_retries = 3
        self.timeout = 30
        
        # Headers to appear more like a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # CSS selectors configuration (modular for easy updates)
        self.selectors = {
            'event_cards': '.event-card, .event-item, [class*="event"]',
            'title': 'h2, h3, .event-title, [class*="title"]',
            'date': '.event-date, .date, [class*="date"]',
            'location': '.event-location, .location, [class*="location"]',
            'category': '.event-category, .category, [class*="category"]',
            'description': '.event-description, .description, p',
            'image': 'img',
            'link': 'a[href]'
        }
        
        self.events = []
        
    def respectful_delay(self):
        """Implement respectful crawling delay"""
        delay = random.uniform(*self.delay_range)
        logger.debug(f"Waiting {delay:.2f} seconds before next request")
        time.sleep(delay)
        
    def make_request(self, url: str, retries: int = 0) -> Optional[requests.Response]:
        """
        Make HTTP request with exponential backoff and retry logic
        
        Args:
            url: URL to request
            retries: Current retry count
            
        Returns:
            Response object or None if failed
        """
        try:
            self.respectful_delay()
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 429:  # Rate limited
                if retries < self.max_retries:
                    wait_time = (2 ** retries) * random.uniform(1, 2)
                    logger.warning(f"Rate limited. Waiting {wait_time:.2f} seconds before retry {retries + 1}")
                    time.sleep(wait_time)
                    return self.make_request(url, retries + 1)
                else:
                    logger.error(f"Max retries exceeded for rate limiting: {url}")
                    return None
                    
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            if retries < self.max_retries:
                wait_time = (2 ** retries) * random.uniform(1, 2)
                logger.warning(f"Request failed: {e}. Retrying in {wait_time:.2f} seconds (attempt {retries + 1})")
                time.sleep(wait_time)
                return self.make_request(url, retries + 1)
            else:
                logger.error(f"Max retries exceeded for {url}: {e}")
                return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove HTML artifacts and normalize whitespace
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Handle common encoding issues
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        return text
    
    def extract_date(self, date_text: str) -> tuple:
        """
        Extract and validate event dates
        
        Returns:
            Tuple of (start_date, end_date) as strings
        """
        if not date_text:
            return "", ""
        
        # Common date patterns
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\w+ \d{1,2}, \d{4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, date_text)
            dates.extend(matches)
        
        # Validate dates are in the future
        valid_dates = []
        for date_str in dates:
            try:
                # Try different date formats
                for fmt in ['%m/%d/%Y', '%B %d, %Y', '%Y-%m-%d']:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        if parsed_date >= datetime.now() - timedelta(days=1):  # Allow today's events
                            valid_dates.append(date_str)
                        break
                    except ValueError:
                        continue
            except:
                continue
        
        start_date = valid_dates[0] if valid_dates else ""
        end_date = valid_dates[1] if len(valid_dates) > 1 else ""
        
        return start_date, end_date
    
    def extract_event_data(self, soup: BeautifulSoup, base_url: str) -> List[Event]:
        """
        Extract event data from the page
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for relative links
            
        Returns:
            List of Event objects
        """
        events = []
        
        # Try multiple selectors to find event containers
        event_containers = None
        for selector in self.selectors['event_cards'].split(', '):
            event_containers = soup.select(selector.strip())
            if event_containers:
                logger.info(f"Found {len(event_containers)} events using selector: {selector}")
                break
        
        if not event_containers:
            logger.warning("No event containers found. Trying fallback approach.")
            # Fallback: look for any containers with event-related text
            event_containers = soup.find_all(['div', 'article', 'section'], 
                                           class_=re.compile(r'event|listing|card', re.I))
        
        for container in event_containers:
            try:
                event = Event()
                event.scraped_at = datetime.now().isoformat()
                
                # Extract title
                title_elem = None
                for selector in self.selectors['title'].split(', '):
                    title_elem = container.select_one(selector.strip())
                    if title_elem:
                        break
                
                if title_elem:
                    event.title = self.clean_text(title_elem.get_text())
                
                # Extract date
                date_elem = None
                for selector in self.selectors['date'].split(', '):
                    date_elem = container.select_one(selector.strip())
                    if date_elem:
                        break
                
                if date_elem:
                    date_text = self.clean_text(date_elem.get_text())
                    event.date_start, event.date_end = self.extract_date(date_text)
                
                # Extract location
                location_elem = None
                for selector in self.selectors['location'].split(', '):
                    location_elem = container.select_one(selector.strip())
                    if location_elem:
                        break
                
                if location_elem:
                    event.location = self.clean_text(location_elem.get_text())
                
                # Extract category
                category_elem = None
                for selector in self.selectors['category'].split(', '):
                    category_elem = container.select_one(selector.strip())
                    if category_elem:
                        break
                
                if category_elem:
                    event.category = self.clean_text(category_elem.get_text())
                
                # Extract description
                desc_elem = None
                for selector in self.selectors['description'].split(', '):
                    desc_elem = container.select_one(selector.strip())
                    if desc_elem:
                        break
                
                if desc_elem:
                    event.description = self.clean_text(desc_elem.get_text())[:500]  # Limit length
                
                # Extract image URL
                img_elem = container.select_one(self.selectors['image'])
                if img_elem:
                    img_src = img_elem.get('src') or img_elem.get('data-src')
                    if img_src:
                        event.image_url = urljoin(base_url, img_src)
                
                # Extract event URL
                link_elem = container.select_one(self.selectors['link'])
                if link_elem:
                    href = link_elem.get('href')
                    if href:
                        event.url = urljoin(base_url, href)
                
                # Only add events with at least a title
                if event.title:
                    events.append(event)
                    logger.debug(f"Extracted event: {event.title}")
                
            except Exception as e:
                logger.warning(f"Error extracting event data: {e}")
                continue
        
        return events
    
    def scrape_events_page(self, url: str) -> List[Event]:
        """
        Scrape events from a single page
        
        Args:
            url: URL to scrape
            
        Returns:
            List of Event objects
        """
        logger.info(f"Scraping events from: {url}")
        
        response = self.make_request(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = self.extract_event_data(soup, url)
        
        logger.info(f"Extracted {len(events)} events from {url}")
        return events
    
    def find_pagination_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Find pagination URLs to scrape additional pages
        
        Args:
            soup: BeautifulSoup object of the current page
            base_url: Base URL for relative links
            
        Returns:
            List of pagination URLs
        """
        pagination_urls = []
        
        # Look for common pagination patterns
        pagination_selectors = [
            '.pagination a',
            '.pager a',
            'a[href*="page"]',
            'a[href*="offset"]',
            '.next',
            '[class*="next"]'
        ]
        
        for selector in pagination_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and 'page' in href.lower():
                    full_url = urljoin(base_url, href)
                    if full_url not in pagination_urls:
                        pagination_urls.append(full_url)
        
        return pagination_urls[:10]  # Limit to prevent infinite crawling
    
    def scrape_all_events(self) -> List[Event]:
        """
        Scrape all events from the site
        
        Returns:
            List of all Event objects
        """
        all_events = []
        urls_to_scrape = [self.events_url]
        scraped_urls = set()
        
        while urls_to_scrape:
            url = urls_to_scrape.pop(0)
            
            if url in scraped_urls:
                continue
            
            scraped_urls.add(url)
            
            # Scrape current page
            page_events = self.scrape_events_page(url)
            all_events.extend(page_events)
            
            # Find pagination URLs (only for first page to avoid too much crawling)
            if len(scraped_urls) == 1:
                response = self.make_request(url)
                if response:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    pagination_urls = self.find_pagination_urls(soup, url)
                    urls_to_scrape.extend(pagination_urls)
                    logger.info(f"Found {len(pagination_urls)} additional pages to scrape")
        
        # Remove duplicates based on title + date + location
        unique_events = []
        seen_events = set()
        
        for event in all_events:
            event_key = (event.title.lower(), event.date_start, event.location.lower())
            if event_key not in seen_events:
                seen_events.add(event_key)
                unique_events.append(event)
            else:
                logger.debug(f"Duplicate event removed: {event.title}")
        
        logger.info(f"Total unique events: {len(unique_events)}")
        return unique_events
    
    def validate_and_clean_events(self, events: List[Event]) -> List[Event]:
        """
        Validate and clean event data according to quality rules
        
        Args:
            events: List of Event objects
            
        Returns:
            List of validated and cleaned Event objects
        """
        cleaned_events = []
        
        for event in events:
            # Skip events without title
            if not event.title:
                continue
            
            # Fill missing fields with defaults
            if not event.date_start:
                event.date_start = "TBD"
            
            if not event.location:
                event.location = "TBD"
            
            if not event.category:
                event.category = "General"
            
            # Validate event URL if present
            if event.url:
                try:
                    parsed = urlparse(event.url)
                    if not parsed.scheme or not parsed.netloc:
                        event.url = ""
                except:
                    event.url = ""
            
            cleaned_events.append(event)
        
        return cleaned_events
    
    def save_to_csv(self, events: List[Event], filename: str = None):
        """Save events to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"iloveny_events_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if not events:
                logger.warning("No events to save to CSV")
                return
            
            fieldnames = list(asdict(events[0]).keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for event in events:
                writer.writerow(asdict(event))
        
        logger.info(f"Saved {len(events)} events to {filepath}")
    
    def save_to_json(self, events: List[Event], filename: str = None):
        """Save events to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"iloveny_events_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        events_data = [asdict(event) for event in events]
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump({
                'scrape_timestamp': datetime.now().isoformat(),
                'total_events': len(events),
                'events': events_data
            }, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(events)} events to {filepath}")
    
    def run_scraper(self, output_format: str = 'both'):
        """
        Run the complete scraping process
        
        Args:
            output_format: 'csv', 'json', or 'both'
        """
        logger.info("Starting iloveny.com events scraper")
        start_time = datetime.now()
        
        try:
            # Scrape all events
            events = self.scrape_all_events()
            
            # Validate and clean events
            events = self.validate_and_clean_events(events)
            
            if not events:
                logger.warning("No events found to save")
                return
            
            # Save results
            if output_format in ['csv', 'both']:
                self.save_to_csv(events)
            
            if output_format in ['json', 'both']:
                self.save_to_json(events)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"Scraping completed successfully!")
            logger.info(f"Total events scraped: {len(events)}")
            logger.info(f"Duration: {duration}")
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise

def main():
    """Main function to run the scraper"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape events from iloveny.com')
    parser.add_argument('--output-dir', default='scraped_data', 
                       help='Output directory for scraped data')
    parser.add_argument('--format', choices=['csv', 'json', 'both'], default='both',
                       help='Output format(s)')
    parser.add_argument('--delay-min', type=float, default=2.0,
                       help='Minimum delay between requests (seconds)')
    parser.add_argument('--delay-max', type=float, default=5.0,
                       help='Maximum delay between requests (seconds)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize and run scraper
    scraper = ILoveNYScraper(
        output_dir=args.output_dir,
        delay_range=(args.delay_min, args.delay_max)
    )
    
    scraper.run_scraper(output_format=args.format)

if __name__ == "__main__":
    main()
