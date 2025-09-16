#!/usr/bin/env python3
"""
Event Data Validator for iloveny.com events
Validates scraped event data according to specified requirements
"""

import re
import requests
from datetime import datetime
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_text(raw_text: str) -> str:
    """
    Normalize text by cleaning HTML artifacts and whitespace
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""

    # Remove HTML tags and entities
    text = re.sub(r"<[^>]+>", "", raw_text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&apos;", "'").replace("&nbsp;", " ")

    # Normalize whitespace
    return re.sub(r"\s+", " ", text.strip())


def validate_event_date(event: Dict[str, Any]) -> bool:
    """
    Validate event date is in the future
    """
    date_fields = ["date", "date_start", "start_date", "event_date", "when"]

    for field in date_fields:
        if field in event and event[field]:
            date_text = str(event[field]).strip().lower()
            if not date_text or date_text in ["tbd", "n/a", "unknown"]:
                continue

            # Check for relative terms first
            if any(
                term in date_text for term in ["now", "ongoing", "current", "today"]
            ):
                return True

            # Try common date patterns
            patterns = [
                r"(\d{4}-\d{2}-\d{2})",  # 2025-11-16 or 2025-09-16T03:59:59.000Z
                r"(\w+\s+\d{1,2},\s+\d{4})",  # Nov 16, 2025
                r"(\d{1,2}/\d{1,2}/\d{4})",  # 11/16/2025
            ]

            for pattern in patterns:
                matches = re.findall(pattern, date_text)
                if matches:
                    date_str = matches[-1]
                    formats = ["%Y-%m-%d", "%b %d, %Y", "%m/%d/%Y"]

                    for fmt in formats:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            return parsed_date.date() >= datetime.now().date()
                        except ValueError:
                            continue

    return False


def validate_location(event: Dict[str, Any]) -> bool:
    """
    Validate event is located in NYC area
    """
    location_fields = ["location", "venue", "address", "where", "city"]

    # Check for region field in udfs_object
    if "udfs_object" in event and event["udfs_object"]:
        for field_id, field_data in event["udfs_object"].items():
            if isinstance(field_data, dict) and field_data.get("name") == "Regions":
                region_value = field_data.get("value", "").lower()
                if region_value in ["hudson valley", "long island", "westchester"]:
                    return True

    # Core NYC identifiers
    nyc_keywords = [
        "manhattan",
        "brooklyn",
        "queens",
        "bronx",
        "staten island",
        "new york city",
        "nyc",
        "new york, ny",
        "new york",
        "times square",
        "central park",
        "broadway",
        "soho",
        "tribeca",
        "chelsea",
        "village",
        "harlem",
        "williamsburg",
        "dumbo",
        # NYC Metro areas
        "hudson valley",
        "westchester",
        "long island",
        "croton on hudson",
        "tarrytown",
        "white plains",
        "yonkers",
        "new rochelle",
        "beacon",
    ]

    for field in location_fields:
        if field in event and event[field]:
            location_text = str(event[field]).lower().strip()

            # Check for NYC keywords
            if any(keyword in location_text for keyword in nyc_keywords):
                return True

            # Check for NY state indicators
            if "new york" in location_text and any(
                indicator in location_text for indicator in [", ny", "ny ", "new york,"]
            ):
                return True

    return False


def detect_duplicates(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect and flag duplicate events
    """
    duplicates = []
    processed = set()

    for i, event1 in enumerate(events):
        if i in processed:
            continue

        title1 = normalize_text(str(event1.get("title", ""))).lower()
        if not title1:
            continue

        for j, event2 in enumerate(events[i + 1:], start=i + 1):
            if j in processed:
                continue

        title2 = normalize_text(str(event2.get("title", ""))).lower()

        # Simple duplicate detection: exact title match
        if title1 == title2:
            duplicates.append(
                {
                    "original_index": i,
                    "duplicate_index": j,
                    "original_event": event1,
                    "duplicate_event": event2,
                    "reason": "exact title match",
                }
            )
            processed.add(j)

    return duplicates


def validate_data_completeness(event: Dict[str, Any]) -> Tuple[Dict[str, bool], str]:
    """
    Check for completeness in title, date, location, and description

    Args:
        event: Event dictionary

    Returns:
        Tuple of (validation dictionary for required fields, summary string)
    """
    required_fields = {
        "title": ["title", "name", "event_name"],
        "date": ["date", "date_start", "start_date", "when", "event_date"],
        "location": ["location", "venue", "where", "address"],
        "description": ["description", "summary", "details", "about"],
    }

    validation_results = {}
    missing_fields = []

    for field_name, possible_keys in required_fields.items():
        field_found = False
        field_value = None

        for key in possible_keys:
            if key in event and event[key]:
                field_value = str(event[key]).strip()
                if field_value and field_value.lower() not in [
                    "",
                    "n/a",
                    "tbd",
                    "unknown",
                    "null",
                    "none",
                ]:
                    field_found = True
                    break

        validation_results[field_name] = field_found

        if not field_found:
            missing_fields.append(field_name)

    # Create summary string
    if not missing_fields:
        summary = "All required fields present"
    else:
        summary = f"Missing required fields: {', '.join(missing_fields)}"

    return validation_results, summary


def validate_links(event: Dict[str, Any]) -> bool:
    """
    Validate event URLs are accessible

    Args:
        event: Event dictionary containing URL information

    Returns:
        Boolean indicating if links are valid and accessible
    """
    url_fields = ["url", "event_url", "link", "website", "more_info"]

    for field in url_fields:
        if field in event and event[field]:
            url = str(event[field]).strip()

            if not url:
                continue

            # Basic URL format validation
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    # Try adding https if missing
                    if not url.startswith(("http://", "https://")):
                        url = "https://" + url
                        parsed = urlparse(url)

                    if not parsed.scheme or not parsed.netloc:
                        continue
            except Exception:
                continue

            # Test URL accessibility
            try:
                response = requests.head(url, timeout=10, allow_redirects=True)
                if response.status_code < 400:
                    return True
            except requests.RequestException:
                # Try GET request as fallback
                try:
                    response = requests.get(url, timeout=10, allow_redirects=True)
                    if response.status_code < 400:
                        return True
                except requests.RequestException:
                    continue

    return False


def validate_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main validation function for list of events

    Args:
        events: List of event dictionaries

    Returns:
        Validation results dictionary containing total events, valid events,
        invalid events, duplicates, and validation errors
    """
    logger.info(f"Starting validation of {len(events)} events")

    validation_results = {
        "total_events": len(events),
        "valid_events": [],
        "invalid_events": [],
        "duplicates": [],
        "validation_errors": [],
        "summary": {},
    }

    # Detect duplicates first
    duplicates = detect_duplicates(events)
    validation_results["duplicates"] = duplicates

    # Get indices of duplicate events to mark them
    duplicate_indices = set()
    for dup in duplicates:
        duplicate_indices.add(dup["duplicate_index"])

    # Validate each event
    for i, event in enumerate(events):
        event_validation = {
            "index": i,
            "event": event,
            "is_duplicate": i in duplicate_indices,
            "validations": {},
            "errors": [],
        }

        try:
            # Run all validations
            event_validation["validations"]["future_date"] = validate_event_date(event)
            event_validation["validations"]["nyc_location"] = validate_location(event)
            event_validation["validations"]["accessible_links"] = validate_links(event)

            # Data completeness validation
            completeness_results, completeness_summary = validate_data_completeness(
                event
            )
            event_validation["validations"]["data_completeness"] = completeness_results
            event_validation["completeness_summary"] = completeness_summary

            # Determine if event is valid overall
            is_valid = (
                event_validation["validations"]["future_date"]
                and event_validation["validations"]["nyc_location"]
                and all(completeness_results.values())  # All required fields present
            )

            # Add to appropriate list
            if is_valid and not event_validation["is_duplicate"]:
                validation_results["valid_events"].append(event_validation)
            else:
                validation_results["invalid_events"].append(event_validation)

                # Record reasons for invalidity
                if not event_validation["validations"]["future_date"]:
                    event_validation["errors"].append("Invalid or past date")
                if not event_validation["validations"]["nyc_location"]:
                    event_validation["errors"].append("Not located in NYC area")
                if not all(completeness_results.values()):
                    event_validation["errors"].append(completeness_summary)
                if event_validation["is_duplicate"]:
                    event_validation["errors"].append("Duplicate event")

        except Exception as e:
            event_validation["errors"].append(f"Validation error: {str(e)}")
            validation_results["invalid_events"].append(event_validation)
            validation_results["validation_errors"].append(
                {"event_index": i, "error": str(e)}
            )

    # Create summary statistics
    validation_results["summary"] = {
        "total_events": len(events),
        "valid_events_count": len(validation_results["valid_events"]),
        "invalid_events_count": len(validation_results["invalid_events"]),
        "duplicates_count": len(duplicates),
        "validation_errors_count": len(validation_results["validation_errors"]),
        "success_rate": (
            len(validation_results["valid_events"]) / len(events) * 100 if events else 0
        ),
    }

    logger.info(
        f"Validation complete: {validation_results['summary']['valid_events_count']}/{len(events)} valid events"
    )

    return validation_results


if __name__ == "__main__":
    # Test data
    sample_events = [
        {
            "title": "The Great Jack O'Lantern Blaze",
            "date": "Now Through Nov 16, 2025",
            "location": "Hudson Valley, Croton on Hudson",
            "description": "Halloween event with carved pumpkins",
            "url": "https://www.iloveny.com/event/great-jack-olantern-blaze",
        },
        {
            "title": "NYC Food Festival",
            "date": "Dec 1, 2025",
            "location": "Manhattan, New York City",
            "description": "Annual food festival in Central Park",
        },
    ]

    # Run validation
    results = validate_events(sample_events)

    print("\n=== VALIDATION RESULTS ===")
    print(f"Total Events: {results['summary']['total_events']}")
    print(f"Valid Events: {results['summary']['valid_events_count']}")
    print(f"Invalid Events: {results['summary']['invalid_events_count']}")
    print(f"Duplicates: {results['summary']['duplicates_count']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
