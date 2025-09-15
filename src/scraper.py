"""
I Love NY Events Scraper

This module implements a web scraper for iloveny.com/events using reverse-engineered API endpoints.
It demonstrates data quality assurance, respectful scraping practices, and business logic integration.
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import csv
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scraper.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ILoveNYScraper:
    """
    Main scraper class for I Love NY events data.

    Implements respectful scraping with exponential backoff, retry limits,
    and comprehensive error handling.
    """

    def __init__(
        self,
        base_url: str = "https://www.iloveny.com",
        retry_limit: int = 3,
        delay: float = 2.0,
    ):
        """
        Initialize the scraper with configuration.

        Args:
            base_url: Base URL for the I Love NY website
            retry_limit: Maximum number of retry attempts
            delay: Base delay between requests in seconds
        """
        self.base_url = base_url
        self.retry_limit = retry_limit
        self.delay = delay
        self.session = requests.Session()
        self.token = None

        # Configure session headers
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Referer": f"{base_url}/events",
            }
        )

    def get_auth_token(self) -> Optional[str]:
        """
        Retrieve authentication token from the API.

        Returns:
            Authentication token string or None if failed
        """
        token_url = f"{self.base_url}/plugins/core/get_simple_token/"

        try:
            response = self.session.get(token_url, timeout=10)
            response.raise_for_status()

            # The response should contain the token
            token = response.text.strip()
            if token:
                self.token = token
                logger.info("Successfully retrieved authentication token")
                return token
            else:
                logger.error("Empty token received")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get auth token: {e}")
            return None

    def exponential_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        return self.delay * (2**attempt) + (0.1 * attempt)

    def make_request_with_retry(
        self, url: str, params: Optional[Dict] = None, method: str = "GET"
    ) -> Optional[requests.Response]:
        """
        Make HTTP request with exponential backoff retry logic.

        Args:
            url: Request URL
            params: Query parameters
            method: HTTP method

        Returns:
            Response object or None if all retries failed
        """
        for attempt in range(self.retry_limit):
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, params=params, timeout=30)
                else:
                    response = self.session.post(url, params=params, timeout=30)

                response.raise_for_status()
                logger.info(f"Successfully made request to {url}")
                return response

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")

                if attempt < self.retry_limit - 1:
                    backoff_delay = self.exponential_backoff(attempt)
                    logger.info(f"Waiting {backoff_delay:.2f} seconds before retry...")
                    time.sleep(backoff_delay)
                else:
                    logger.error(f"All {self.retry_limit} attempts failed for {url}")

        return None

    def build_events_query(
        self, start_date: str, end_date: str, limit: int = 12, skip: int = 0
    ) -> Dict:
        """
        Build the query parameters for the events API.

        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format
            limit: Number of events to retrieve
            skip: Number of events to skip (for pagination)

        Returns:
            Query parameters dictionary
        """
        # Category IDs from the original request
        category_ids = [
            "3",
            "5",
            "6",
            "106",
            "74",
            "97",
            "31",
            "100",
            "10",
            "101",
            "102",
            "87",
            "29",
            "11",
            "12",
            "14",
            "15",
            "113",
            "18",
            "98",
            "99",
            "111",
            "26",
            "30",
        ]

        query_data = {
            "filter": {
                "solrOptions": {},
                "primary_site": "primary",
                "categories.catId": {"$in": category_ids},
                "date_range": {
                    "start": {"$date": start_date},
                    "end": {"$date": end_date},
                },
            },
            "options": {
                "skip": skip,
                "limit": limit,
                "hooks": ["afterFind_listing", "afterFind_host"],
                "sort": {"featured": -1, "date": 1, "rank": 1, "title": 1},
                "fields": {
                    "accountId": 1,
                    "categories": 1,
                    "detailURL": 1,
                    "featured": 1,
                    "host_id": 1,
                    "host.recid": 1,
                    "host.title": 1,
                    "host.detailURL": 1,
                    "latitude": 1,
                    "listing": 1,
                    "listing_id": 1,
                    "listing.recid": 1,
                    "listing.title": 1,
                    "listing.detailURL": 1,
                    "listing.region": 1,
                    "address1": 1,
                    "location": 1,
                    "longitude": 1,
                    "media_raw": 1,
                    "nextDate": 1,
                    "primary_site": 1,
                    "rank": 1,
                    "recId": 1,
                    "recid": 1,
                    "recurType": 1,
                    "recurrence": 1,
                    "startDate": 1,
                    "endDate": 1,
                    "startTime": 1,
                    "endTime": 1,
                    "title": 1,
                    "description": 1,
                    "typeName": 1,
                    "loc": 1,
                    "url": 1,
                    "date": 1,
                    "city": 1,
                    "udfs_object": 1,
                    "ticketmaster": 1,
                    "linkUrl": 1,
                    "hostname": 1,
                },
                "count": True,
            },
        }

        return {"json": json.dumps(query_data), "token": self.token}

    def fetch_events(
        self, start_date: str, end_date: str, limit: int = 12, skip: int = 0
    ) -> Optional[List[Dict]]:
        """
        Fetch events data from the API.

        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format
            limit: Number of events to retrieve
            skip: Number of events to skip

        Returns:
            List of event dictionaries or None if failed
        """
        if not self.token:
            logger.error("No authentication token available")
            return None

        events_url = (
            f"{self.base_url}/includes/rest_v2/plugins_events_events_by_date/find/"
        )
        params = self.build_events_query(start_date, end_date, limit, skip)

        response = self.make_request_with_retry(events_url, params)
        if not response:
            return None

        try:
            data = response.json()
            logger.debug(f"Response data type: {type(data)}")
            logger.debug(
                f"Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}"
            )

            if isinstance(data, dict):
                # The response contains 'docs' which is a dict with 'count' and 'docs' keys
                docs_data = data.get("docs", {})
                if isinstance(docs_data, dict):
                    events = docs_data.get("docs", [])
                else:
                    events = []
            else:
                events = []
            logger.info(f"Retrieved {len(events)} events")
            return events
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None

    def scrape_events(
        self, days_ahead: int = 30, output_format: str = "json"
    ) -> List[Dict]:
        """
        Main method to scrape events for the specified number of days ahead.

        Args:
            days_ahead: Number of days to look ahead
            output_format: Output format ('json' or 'csv')

        Returns:
            List of processed events
        """
        logger.info(f"Starting event scraping for {days_ahead} days ahead")

        # Get authentication token
        if not self.get_auth_token():
            logger.error("Failed to get authentication token")
            return []

        # Calculate date range - API requires dates at 04:00:00 (4-hour offset)
        # This appears to be Eastern Time (UTC-4 or UTC-5 depending on DST)
        start_date = datetime.now().replace(hour=4, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=days_ahead)

        start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        logger.info(f"Scraping events from {start_iso} to {end_iso}")

        all_events = []
        skip = 0
        limit = 12

        while True:
            events = self.fetch_events(start_iso, end_iso, limit, skip)
            if not events:
                break

            all_events.extend(events)

            # If we got fewer events than the limit, we've reached the end
            if len(events) < limit:
                break

            skip += limit

            # Respectful delay between requests
            time.sleep(self.delay)

        logger.info(f"Total events scraped: {len(all_events)}")

        # Export data
        self.export_events(all_events, output_format)

        return all_events

    def export_events(self, events: List[Dict], output_format: str = "json") -> None:
        """
        Export events data to file.

        Args:
            events: List of event dictionaries
            output_format: Output format ('json' or 'csv')
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if output_format.lower() == "json":
            filename = f"data/raw/events_{timestamp}.json"
            os.makedirs("data", exist_ok=True)

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2, ensure_ascii=False)

            logger.info(f"Events exported to {filename}")

        elif output_format.lower() == "csv":
            filename = f"data/raw/events_{timestamp}.csv"
            os.makedirs("data", exist_ok=True)

            if events:
                fieldnames = events[0].keys()
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(events)

                logger.info(f"Events exported to {filename}")

def main():
    """
    Main function to run the scraper.
    """
    scraper = ILoveNYScraper(retry_limit=3, delay=2.0)

    # Scrape events for the next 30 days
    events = scraper.scrape_events(days_ahead=1, output_format="json")

    if events:
        print(f"Successfully scraped {len(events)} events")

        # Display sample event
        if events and len(events) > 0:
            sample_event = events[0]
            print("\nSample event:")
            print(f"Title: {sample_event.get('title', 'N/A')}")
            print(f"Date: {sample_event.get('startDate', 'N/A')}")
            print(f"Location: {sample_event.get('address1', 'N/A')}")
            print(f"City: {sample_event.get('city', 'N/A')}")
            print(
                f"Categories: {[cat.get('catName', '') for cat in sample_event.get('categories', [])]}"
            )
    else:
        print("No events were scraped")


if __name__ == "__main__":
    main()
