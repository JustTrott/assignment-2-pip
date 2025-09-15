#!/usr/bin/env python3
"""
Event Data Validator for iloveny.com events
Validates scraped event data according to specified requirements
"""

import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_text(raw_text: str) -> str:
    """
    Normalize text by cleaning HTML artifacts and whitespace
    
    Args:
        raw_text: Raw text string that may contain HTML or extra whitespace
        
    Returns:
        Normalized text string
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', raw_text)
    
    # Remove HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
        '&nbsp;': ' ',
        '&#39;': "'",
        '&mdash;': '—',
        '&ndash;': '–'
    }
    
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove extra punctuation artifacts
    text = re.sub(r'[^\w\s\-.,!?:;()\'\"&@#$%]', '', text)
    
    return text.strip()

def validate_event_date(event: Dict[str, Any]) -> bool:
    """
    Validate event date is in the future
    
    Args:
        event: Event dictionary containing date information
        
    Returns:
        Boolean indicating if date is valid (future date)
    """
    date_fields = ['date', 'date_start', 'start_date', 'event_date', 'when']
    
    for field in date_fields:
        if field in event and event[field]:
            date_text = str(event[field]).strip()
            if not date_text or date_text.lower() in ['tbd', 'tbد', 'n/a', 'unknown']:
                continue
            
            # Common date patterns to try
            date_patterns = [
                # "Now Through Nov 16, 2025"
                r'through\s+(\w+\s+\d{1,2},\s+\d{4})',
                r'until\s+(\w+\s+\d{1,2},\s+\d{4})',
                r'ending\s+(\w+\s+\d{1,2},\s+\d{4})',
                # "Nov 16, 2025"
                r'(\w+\s+\d{1,2},\s+\d{4})',
                # "2025-11-16"
                r'(\d{4}-\d{2}-\d{2})',
                # "11/16/2025"
                r'(\d{1,2}/\d{1,2}/\d{4})',
                # "16 Nov 2025"
                r'(\d{1,2}\s+\w+\s+\d{4})',
            ]
            
            # Try to extract and parse date
            for pattern in date_patterns:
                matches = re.findall(pattern, date_text, re.IGNORECASE)
                if matches:
                    date_str = matches[-1]  # Get the last/end date if multiple
                    
                    # Try different date formats
                    date_formats = [
                        '%B %d, %Y',    # November 16, 2025
                        '%b %d, %Y',    # Nov 16, 2025
                        '%Y-%m-%d',     # 2025-11-16
                        '%m/%d/%Y',     # 11/16/2025
                        '%d %B %Y',     # 16 November 2025
                        '%d %b %Y',     # 16 Nov 2025
                    ]
                    
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            # Check if date is in the future (allow today)
                            return parsed_date.date() >= datetime.now().date()
                        except ValueError:
                            continue
            
            # If no specific date found, check for relative terms
            if any(term in date_text.lower() for term in ['now', 'ongoing', 'current', 'today']):
                return True
    
    # If no valid date found, consider it invalid
    return False

def validate_location(event: Dict[str, Any]) -> bool:
    """
    Validate event is located in NYC (New York City area)
    
    Args:
        event: Event dictionary containing location information
        
    Returns:
        Boolean indicating if location is in NYC area
    """
    location_fields = ['location', 'venue', 'address', 'where', 'city']
    
    # NYC keywords and areas
    nyc_keywords = [
        # Boroughs
        'manhattan', 'brooklyn', 'queens', 'bronx', 'staten island',
        # NYC alternative names
        'new york city', 'nyc', 'new york, ny',
        # Common NYC neighborhoods/areas
        'times square', 'central park', 'wall street', 'broadway',
        'soho', 'tribeca', 'chelsea', 'village', 'harlem',
        'williamsburg', 'dumbo', 'park slope', 'astoria',
        'flushing', 'long island city', 'forest hills'
    ]
    
    # New York State areas that are commonly considered NYC metro
    ny_metro_keywords = [
        'long island', 'westchester', 'hudson valley',
        'white plains', 'yonkers', 'new rochelle'
    ]
    
    for field in location_fields:
        if field in event and event[field]:
            location_text = str(event[field]).lower().strip()
            
            # Direct NYC matches
            for keyword in nyc_keywords:
                if keyword in location_text:
                    return True
            
            # NYC metro area matches (also count as NYC for events)
            for keyword in ny_metro_keywords:
                if keyword in location_text:
                    return True
            
            # Check for New York state with city indicators
            if 'new york' in location_text and any(indicator in location_text 
                for indicator in [', ny', 'ny ', 'new york,']):
                return True
    
    return False

def detect_duplicates(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect and flag duplicate events
    
    Args:
        events: List of event dictionaries
        
    Returns:
        List of duplicate events with similarity information
    """
    duplicates = []
    processed = set()
    
    for i, event1 in enumerate(events):
        if i in processed:
            continue
            
        # Get normalized comparison values
        title1 = normalize_text(str(event1.get('title', ''))).lower()
        date1 = normalize_text(str(event1.get('date', '') or event1.get('date_start', ''))).lower()
        location1 = normalize_text(str(event1.get('location', ''))).lower()
        
        if not title1:  # Skip events without titles
            continue
        
        duplicates_for_event1 = []
        
        for j, event2 in enumerate(events[i+1:], start=i+1):
            if j in processed:
                continue
                
            title2 = normalize_text(str(event2.get('title', ''))).lower()
            date2 = normalize_text(str(event2.get('date', '') or event2.get('date_start', ''))).lower()
            location2 = normalize_text(str(event2.get('location', ''))).lower()
            
            # Check for exact title match
            exact_title_match = title1 == title2
            
            # Check for similar title (>80% similarity using simple word overlap)
            title_similarity = calculate_text_similarity(title1, title2)
            similar_title = title_similarity > 0.8
            
            # Check for same date
            same_date = date1 == date2
            
            # Check for same location
            same_location = location1 == location2
            
            # Determine if duplicate
            is_duplicate = False
            duplicate_reason = []
            
            if exact_title_match and (same_date or same_location):
                is_duplicate = True
                duplicate_reason.append("exact title match")
                
            elif similar_title and same_date and same_location:
                is_duplicate = True
                duplicate_reason.append("similar title with same date and location")
                
            elif exact_title_match and not date1 and not date2:
                is_duplicate = True
                duplicate_reason.append("exact title match (no dates to compare)")
            
            if is_duplicate:
                duplicates_for_event1.append({
                    'original_index': i,
                    'duplicate_index': j,
                    'original_event': event1,
                    'duplicate_event': event2,
                    'similarity_score': title_similarity,
                    'reason': ', '.join(duplicate_reason),
                    'exact_title_match': exact_title_match,
                    'same_date': same_date,
                    'same_location': same_location
                })
                processed.add(j)
        
        if duplicates_for_event1:
            processed.add(i)
            duplicates.extend(duplicates_for_event1)
    
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
        'title': ['title', 'name', 'event_name'],
        'date': ['date', 'date_start', 'start_date', 'when', 'event_date'],
        'location': ['location', 'venue', 'where', 'address'],
        'description': ['description', 'summary', 'details', 'about']
    }
    
    validation_results = {}
    missing_fields = []
    
    for field_name, possible_keys in required_fields.items():
        field_found = False
        field_value = None
        
        for key in possible_keys:
            if key in event and event[key]:
                field_value = str(event[key]).strip()
                if field_value and field_value.lower() not in ['', 'n/a', 'tbd', 'unknown', 'null', 'none']:
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
    url_fields = ['url', 'event_url', 'link', 'website', 'more_info']
    
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
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
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
        'total_events': len(events),
        'valid_events': [],
        'invalid_events': [],
        'duplicates': [],
        'validation_errors': [],
        'summary': {}
    }
    
    # Detect duplicates first
    duplicates = detect_duplicates(events)
    validation_results['duplicates'] = duplicates
    
    # Get indices of duplicate events to mark them
    duplicate_indices = set()
    for dup in duplicates:
        duplicate_indices.add(dup['duplicate_index'])
    
    # Validate each event
    for i, event in enumerate(events):
        event_validation = {
            'index': i,
            'event': event,
            'is_duplicate': i in duplicate_indices,
            'validations': {},
            'errors': []
        }
        
        try:
            # Run all validations
            event_validation['validations']['future_date'] = validate_event_date(event)
            event_validation['validations']['nyc_location'] = validate_location(event)
            event_validation['validations']['accessible_links'] = validate_links(event)
            
            # Data completeness validation
            completeness_results, completeness_summary = validate_data_completeness(event)
            event_validation['validations']['data_completeness'] = completeness_results
            event_validation['completeness_summary'] = completeness_summary
            
            # Determine if event is valid overall
            is_valid = (
                event_validation['validations']['future_date'] and
                event_validation['validations']['nyc_location'] and
                all(completeness_results.values())  # All required fields present
            )
            
            # Add to appropriate list
            if is_valid and not event_validation['is_duplicate']:
                validation_results['valid_events'].append(event_validation)
            else:
                validation_results['invalid_events'].append(event_validation)
                
                # Record reasons for invalidity
                if not event_validation['validations']['future_date']:
                    event_validation['errors'].append("Invalid or past date")
                if not event_validation['validations']['nyc_location']:
                    event_validation['errors'].append("Not located in NYC area")
                if not all(completeness_results.values()):
                    event_validation['errors'].append(completeness_summary)
                if event_validation['is_duplicate']:
                    event_validation['errors'].append("Duplicate event")
                    
        except Exception as e:
            event_validation['errors'].append(f"Validation error: {str(e)}")
            validation_results['invalid_events'].append(event_validation)
            validation_results['validation_errors'].append({
                'event_index': i,
                'error': str(e)
            })
    
    # Create summary statistics
    validation_results['summary'] = {
        'total_events': len(events),
        'valid_events_count': len(validation_results['valid_events']),
        'invalid_events_count': len(validation_results['invalid_events']),
        'duplicates_count': len(duplicates),
        'validation_errors_count': len(validation_results['validation_errors']),
        'success_rate': len(validation_results['valid_events']) / len(events) * 100 if events else 0
    }
    
    logger.info(f"Validation complete: {validation_results['summary']['valid_events_count']}/{len(events)} valid events")
    
    return validation_results

# Example usage and testing
if __name__ == "__main__":
    # Test data
    sample_events = [
        {
            'title': 'The Great Jack O\'Lantern Blaze',
            'date': 'Now Through Nov 16, 2025',
            'location': 'Hudson Valley, Croton on Hudson',
            'description': 'Halloween event with carved pumpkins',
            'url': 'https://www.iloveny.com/event/great-jack-olantern-blaze'
        },
        {
            'title': 'NYC Food Festival',
            'date': 'Dec 1, 2025',
            'location': 'Manhattan, New York City',
            'description': 'Annual food festival in Central Park'
        }
    ]
    
    # Run validation
    results = validate_events(sample_events)
    
    print("\n=== VALIDATION RESULTS ===")
    print(f"Total Events: {results['summary']['total_events']}")
    print(f"Valid Events: {results['summary']['valid_events_count']}")
    print(f"Invalid Events: {results['summary']['invalid_events_count']}")
    print(f"Duplicates: {results['summary']['duplicates_count']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
