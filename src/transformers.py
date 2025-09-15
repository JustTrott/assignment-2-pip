#!/usr/bin/env python3
"""
Event Data Transformation Pipeline
Transforms validated event data for business intelligence and export
"""

import json
import csv
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventTransformer:
    """Data transformation pipeline for validated events"""
    
    def __init__(self, output_dir: str = "transformed_data"):
        """Initialize transformer with output directory"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Business rules configuration
        self.business_rules = {
            'priority_keywords': ['featured', 'premium', 'vip', 'exclusive'],
            'seasonal_categories': {
                'fall': ['halloween', 'autumn', 'harvest', 'pumpkin', 'october', 'november'],
                'winter': ['holiday', 'christmas', 'new year', 'december', 'january', 'february'],
                'spring': ['easter', 'spring', 'march', 'april', 'may'],
                'summer': ['summer', 'beach', 'outdoor', 'june', 'july', 'august']
            },
            'min_description_length': 50,
            'max_future_days': 365
        }
        
        # Category mapping for standardization
        self.category_mapping = {
            'food & drink': 'Food & Beverage',
            'local food & drink': 'Food & Beverage',
            'dining': 'Food & Beverage',
            'restaurant': 'Food & Beverage',
            'music': 'Entertainment',
            'concert': 'Entertainment',
            'show': 'Entertainment',
            'theater': 'Entertainment',
            'theatre': 'Entertainment',
            'sports': 'Sports & Recreation',
            'recreation': 'Sports & Recreation',
            'outdoor': 'Sports & Recreation',
            'festival': 'Festivals',
            'fair': 'Festivals',
            'celebration': 'Festivals',
            'art': 'Arts & Culture',
            'museum': 'Arts & Culture',
            'gallery': 'Arts & Culture',
            'culture': 'Arts & Culture',
            'education': 'Educational',
            'workshop': 'Educational',
            'class': 'Educational',
            'business': 'Business',
            'networking': 'Business',
            'conference': 'Business'
        }
    
    def normalize_event_data(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize event data with consistent formatting and structure
        
        Args:
            event: Raw event dictionary
            
        Returns:
            Normalized event dictionary
        """
        normalized = {}
        
        # Normalize title
        title = event.get('title', '').strip()
        normalized['title'] = self._clean_title(title)
        
        # Normalize dates
        normalized.update(self._normalize_dates(event))
        
        # Normalize location
        normalized.update(self._normalize_location(event))
        
        # Normalize description
        description = event.get('description', '') or event.get('summary', '')
        normalized['description'] = self._clean_text(description)
        
        # Normalize URLs
        normalized['event_url'] = self._normalize_url(event.get('url', '') or event.get('event_url', ''))
        normalized['image_url'] = self._normalize_url(event.get('image_url', ''))
        
        # Preserve original data
        normalized['original_data'] = event
        normalized['processed_at'] = datetime.now().isoformat()
        
        return normalized
    
    def enrich_event_data(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich event data with additional computed fields and metadata
        
        Args:
            event: Normalized event dictionary
            
        Returns:
            Enriched event dictionary
        """
        enriched = event.copy()
        
        # Add event timing metadata
        enriched.update(self._add_timing_metadata(event))
        
        # Add location metadata
        enriched.update(self._add_location_metadata(event))
        
        # Add content analysis
        enriched.update(self._analyze_content(event))
        
        # Add event scoring
        enriched['quality_score'] = self._calculate_quality_score(event)
        enriched['popularity_indicators'] = self._extract_popularity_indicators(event)
        
        # Add seasonal information
        enriched['season'] = self._determine_season(event)
        
        return enriched
    
    def calculate_business_metrics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate business metrics from transformed events
        
        Args:
            events: List of enriched event dictionaries
            
        Returns:
            Dictionary containing business metrics
        """
        if not events:
            return {}
        
        metrics = {
            'total_events': len(events),
            'date_coverage': self._calculate_date_coverage(events),
            'location_distribution': self._calculate_location_distribution(events),
            'category_distribution': self._calculate_category_distribution(events),
            'quality_metrics': self._calculate_quality_metrics(events),
            'temporal_metrics': self._calculate_temporal_metrics(events),
            'content_metrics': self._calculate_content_metrics(events)
        }
        
        return metrics
    
    def categorize_event(self, event: Dict[str, Any]) -> str:
        """
        Categorize event based on content analysis and business rules
        
        Args:
            event: Event dictionary
            
        Returns:
            Standardized category string
        """
        # Get existing category
        existing_category = event.get('category', '').lower().strip()
        
        # Check category mapping first
        if existing_category in self.category_mapping:
            return self.category_mapping[existing_category]
        
        # Analyze title and description for keywords
        text_to_analyze = (
            event.get('title', '') + ' ' + 
            event.get('description', '') + ' ' +
            existing_category
        ).lower()
        
        # Score categories based on keyword presence
        category_scores = {}
        
        for category, keywords in {
            'Food & Beverage': ['food', 'drink', 'restaurant', 'dining', 'cuisine', 'chef', 'wine', 'beer'],
            'Entertainment': ['music', 'concert', 'show', 'performance', 'band', 'singer', 'comedy'],
            'Sports & Recreation': ['sport', 'game', 'run', 'walk', 'bike', 'outdoor', 'recreation'],
            'Festivals': ['festival', 'fair', 'celebration', 'parade', 'carnival'],
            'Arts & Culture': ['art', 'museum', 'gallery', 'exhibition', 'culture', 'history'],
            'Educational': ['workshop', 'class', 'seminar', 'learning', 'education', 'training'],
            'Business': ['business', 'networking', 'conference', 'meeting', 'professional'],
            'Family': ['family', 'kids', 'children', 'child']
        }.items():
            score = sum(1 for keyword in keywords if keyword in text_to_analyze)
            if score > 0:
                category_scores[category] = score
        
        # Return highest scoring category or default
        if category_scores:
            return max(category_scores.keys(), key=lambda k: category_scores[k])
        
        return 'General'
    
    def format_for_export(self, event: Dict[str, Any], export_format: str = 'standard') -> Dict[str, Any]:
        """
        Format event for specific export requirements
        
        Args:
            event: Enriched event dictionary
            export_format: Format type ('standard', 'minimal', 'detailed')
            
        Returns:
            Formatted event dictionary
        """
        if export_format == 'minimal':
            return {
                'id': event.get('event_id', ''),
                'title': event.get('title', ''),
                'date': event.get('formatted_date', ''),
                'location': event.get('location_name', ''),
                'category': event.get('standardized_category', ''),
                'url': event.get('event_url', '')
            }
        
        elif export_format == 'detailed':
            return event  # Return full enriched event
        
        else:  # standard format
            return {
                'event_id': event.get('event_id', ''),
                'title': event.get('title', ''),
                'description': event.get('description', ''),
                'start_date': event.get('start_date', ''),
                'end_date': event.get('end_date', ''),
                'location_name': event.get('location_name', ''),
                'venue': event.get('venue', ''),
                'borough': event.get('borough', ''),
                'standardized_category': event.get('standardized_category', ''),
                'season': event.get('season', ''),
                'event_url': event.get('event_url', ''),
                'image_url': event.get('image_url', ''),
                'quality_score': event.get('quality_score', 0),
                'is_featured': event.get('is_featured', False),
                'days_until_event': event.get('days_until_event', 0),
                'duration_days': event.get('duration_days', 1),
                'processed_at': event.get('processed_at', '')
            }
    
    def apply_business_rules(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply business rules and filters to events
        
        Args:
            event: Event dictionary
            
        Returns:
            Event with business rules applied, or None if filtered out
        """
        processed_event = event.copy()
        
        # Rule 1: Mark priority events
        title_desc = (event.get('title', '') + ' ' + event.get('description', '')).lower()
        processed_event['is_priority'] = any(keyword in title_desc 
                                           for keyword in self.business_rules['priority_keywords'])
        
        # Rule 2: Filter out events too far in the future
        days_until = event.get('days_until_event', 0)
        if days_until > self.business_rules['max_future_days']:
            processed_event['filtered_reason'] = 'Too far in future'
            processed_event['include_in_export'] = False
        else:
            processed_event['include_in_export'] = True
        
        # Rule 3: Mark events with insufficient description
        description_length = len(event.get('description', ''))
        processed_event['has_rich_content'] = description_length >= self.business_rules['min_description_length']
        
        # Rule 4: Add promotional tags
        processed_event['promotional_tags'] = self._generate_promotional_tags(event)
        
        # Rule 5: Set business priority score
        processed_event['business_priority'] = self._calculate_business_priority(event)
        
        return processed_event
    
    def transform_events(self, validated_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main transformation pipeline - processes all events
        
        Args:
            validated_events: List of validated event dictionaries
            
        Returns:
            Dictionary containing transformed events and metadata
        """
        logger.info(f"Starting transformation of {len(validated_events)} events")
        
        transformed_events = []
        skipped_events = []
        
        for i, event in enumerate(validated_events):
            try:
                # Step 1: Normalize data
                normalized = self.normalize_event_data(event)
                
                # Step 2: Enrich with metadata
                enriched = self.enrich_event_data(normalized)
                
                # Step 3: Categorize
                enriched['standardized_category'] = self.categorize_event(enriched)
                
                # Step 4: Apply business rules
                processed = self.apply_business_rules(enriched)
                
                # Step 5: Add unique ID
                processed['event_id'] = f"event_{i+1:05d}_{hash(processed['title']) % 10000:04d}"
                
                if processed.get('include_in_export', True):
                    transformed_events.append(processed)
                else:
                    skipped_events.append(processed)
                
            except Exception as e:
                logger.warning(f"Error transforming event {i}: {e}")
                skipped_events.append({
                    'original_event': event,
                    'error': str(e),
                    'index': i
                })
        
        # Calculate business metrics
        business_metrics = self.calculate_business_metrics(transformed_events)
        
        transformation_result = {
            'transformed_events': transformed_events,
            'skipped_events': skipped_events,
            'business_metrics': business_metrics,
            'transformation_metadata': {
                'total_input_events': len(validated_events),
                'successfully_transformed': len(transformed_events),
                'skipped_events': len(skipped_events),
                'transformation_timestamp': datetime.now().isoformat(),
                'success_rate': len(transformed_events) / len(validated_events) * 100 if validated_events else 0
            }
        }
        
        logger.info(f"Transformation complete: {len(transformed_events)}/{len(validated_events)} events processed")
        
        return transformation_result
    
    def export_events(self, transformation_result: Dict[str, Any], 
                     formats: List[str] = None, export_format: str = 'standard') -> Dict[str, str]:
        """
        Export transformed events to various formats
        
        Args:
            transformation_result: Result from transform_events()
            formats: List of export formats ['json', 'csv', 'xlsx'] 
            export_format: Data format ('standard', 'minimal', 'detailed')
            
        Returns:
            Dictionary mapping format to output file path
        """
        if formats is None:
            formats = ['json', 'csv']
        
        events = transformation_result['transformed_events']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_paths = {}
        
        # Format events for export
        formatted_events = [self.format_for_export(event, export_format) for event in events]
        
        # JSON export
        if 'json' in formats:
            json_path = self.output_dir / f"transformed_events_{timestamp}.json"
            export_data = {
                'events': formatted_events,
                'metadata': transformation_result['transformation_metadata'],
                'business_metrics': transformation_result['business_metrics']
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            export_paths['json'] = str(json_path)
            logger.info(f"JSON export saved to: {json_path}")
        
        # CSV export
        if 'csv' in formats and formatted_events:
            csv_path = self.output_dir / f"transformed_events_{timestamp}.csv"
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=formatted_events[0].keys())
                writer.writeheader()
                writer.writerows(formatted_events)
            
            export_paths['csv'] = str(csv_path)
            logger.info(f"CSV export saved to: {csv_path}")
        
        # Business metrics export
        if 'metrics' in formats:
            metrics_path = self.output_dir / f"business_metrics_{timestamp}.json"
            
            with open(metrics_path, 'w', encoding='utf-8') as f:
                json.dump(transformation_result['business_metrics'], f, indent=2, default=str)
            
            export_paths['metrics'] = str(metrics_path)
            logger.info(f"Metrics export saved to: {metrics_path}")
        
        return export_paths
    
    # Helper methods
    def _clean_title(self, title: str) -> str:
        """Clean and normalize event title"""
        if not title:
            return ""
        
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title.strip())
        
        # Title case for better presentation
        title = title.title()
        
        return title
    
    def _normalize_dates(self, event: Dict[str, Any]) -> Dict[str, str]:
        """Extract and normalize date information"""
        date_info = {}
        
        # Get raw date text
        raw_date = event.get('date', '') or event.get('date_text', '')
        date_info['raw_date_text'] = raw_date
        
        # Try to parse structured dates
        start_date, end_date = self._parse_dates(raw_date)
        date_info['start_date'] = start_date
        date_info['end_date'] = end_date
        date_info['formatted_date'] = self._format_date_range(start_date, end_date)
        
        return date_info
    
    def _normalize_location(self, event: Dict[str, Any]) -> Dict[str, str]:
        """Normalize location information"""
        location_info = {}
        
        raw_location = event.get('location', '') or event.get('venue', '')
        location_info['raw_location'] = raw_location
        
        # Parse location components
        if raw_location:
            parts = [part.strip() for part in raw_location.split(',')]
            
            if len(parts) >= 2:
                location_info['location_name'] = parts[0]
                location_info['venue'] = parts[-1] if len(parts) > 1 else ''
                location_info['borough'] = self._identify_borough(raw_location)
            else:
                location_info['location_name'] = raw_location
                location_info['venue'] = ''
                location_info['borough'] = self._identify_borough(raw_location)
        
        return location_info
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL format"""
        if not url:
            return ""
        
        url = url.strip()
        
        # Add protocol if missing
        if url and not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def _parse_dates(self, date_text: str) -> tuple:
        """Parse date text into start and end dates"""
        if not date_text:
            return "", ""
        
        # Implementation would parse various date formats
        # For now, return simplified version
        return date_text, ""
    
    def _format_date_range(self, start_date: str, end_date: str) -> str:
        """Format date range for display"""
        if start_date and end_date:
            return f"{start_date} - {end_date}"
        elif start_date:
            return start_date
        else:
            return "Date TBD"
    
    def _identify_borough(self, location: str) -> str:
        """Identify NYC borough from location text"""
        location_lower = location.lower()
        
        boroughs = {
            'manhattan': ['manhattan', 'midtown', 'downtown', 'uptown', 'soho', 'tribeca'],
            'brooklyn': ['brooklyn', 'williamsburg', 'dumbo', 'park slope'],
            'queens': ['queens', 'astoria', 'flushing', 'long island city'],
            'bronx': ['bronx'],
            'staten island': ['staten island']
        }
        
        for borough, keywords in boroughs.items():
            if any(keyword in location_lower for keyword in keywords):
                return borough.title()
        
        return 'Other'
    
    def _add_timing_metadata(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Add timing-related metadata"""
        timing_data = {}
        
        # Calculate days until event (simplified)
        timing_data['days_until_event'] = 30  # Placeholder
        timing_data['duration_days'] = 1  # Placeholder
        timing_data['is_upcoming'] = True
        
        return timing_data
    
    def _add_location_metadata(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Add location-related metadata"""
        return {
            'is_outdoor_event': 'outdoor' in event.get('description', '').lower(),
            'requires_reservation': any(word in event.get('description', '').lower() 
                                      for word in ['reservation', 'booking', 'ticket'])
        }
    
    def _analyze_content(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze event content for insights"""
        description = event.get('description', '')
        
        return {
            'description_length': len(description),
            'has_contact_info': '@' in description or 'phone' in description.lower(),
            'mentions_price': any(word in description.lower() 
                                for word in ['free', 'price', '$', 'cost', 'ticket'])
        }
    
    def _calculate_quality_score(self, event: Dict[str, Any]) -> float:
        """Calculate quality score for event"""
        score = 0.0
        
        # Title quality (0-2 points)
        if event.get('title'):
            score += 2.0 if len(event['title']) > 10 else 1.0
        
        # Description quality (0-3 points)
        desc_len = len(event.get('description', ''))
        if desc_len > 100:
            score += 3.0
        elif desc_len > 50:
            score += 2.0
        elif desc_len > 0:
            score += 1.0
        
        # Image presence (0-1 point)
        if event.get('image_url'):
            score += 1.0
        
        # URL presence (0-1 point)
        if event.get('event_url'):
            score += 1.0
        
        return min(score, 10.0)  # Cap at 10
    
    def _extract_popularity_indicators(self, event: Dict[str, Any]) -> List[str]:
        """Extract popularity indicators from event"""
        indicators = []
        
        text = (event.get('title', '') + ' ' + event.get('description', '')).lower()
        
        if 'featured' in text:
            indicators.append('featured')
        if 'popular' in text:
            indicators.append('popular')
        if 'sold out' in text:
            indicators.append('high_demand')
        
        return indicators
    
    def _determine_season(self, event: Dict[str, Any]) -> str:
        """Determine season for the event"""
        text = (event.get('title', '') + ' ' + event.get('description', '')).lower()
        
        for season, keywords in self.business_rules['seasonal_categories'].items():
            if any(keyword in text for keyword in keywords):
                return season.title()
        
        return 'General'
    
    def _calculate_date_coverage(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate date coverage metrics"""
        return {'total_days_covered': 365}  # Placeholder
    
    def _calculate_location_distribution(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate location distribution"""
        locations = {}
        for event in events:
            borough = event.get('borough', 'Other')
            locations[borough] = locations.get(borough, 0) + 1
        return locations
    
    def _calculate_category_distribution(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate category distribution"""
        categories = {}
        for event in events:
            category = event.get('standardized_category', 'General')
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _calculate_quality_metrics(self, events: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate quality metrics"""
        scores = [event.get('quality_score', 0) for event in events]
        return {
            'average_quality_score': sum(scores) / len(scores) if scores else 0,
            'high_quality_events': len([s for s in scores if s >= 7])
        }
    
    def _calculate_temporal_metrics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate temporal distribution metrics"""
        return {
            'events_next_30_days': len([e for e in events if e.get('days_until_event', 0) <= 30]),
            'average_lead_time': 45  # Placeholder
        }
    
    def _calculate_content_metrics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate content quality metrics"""
        return {
            'events_with_images': len([e for e in events if e.get('image_url')]),
            'events_with_rich_content': len([e for e in events if e.get('has_rich_content')])
        }
    
    def _generate_promotional_tags(self, event: Dict[str, Any]) -> List[str]:
        """Generate promotional tags for marketing"""
        tags = []
        
        if event.get('is_priority'):
            tags.append('featured')
        
        if event.get('quality_score', 0) >= 8:
            tags.append('premium')
        
        season = event.get('season', '').lower()
        if season != 'general':
            tags.append(f'seasonal_{season}')
        
        return tags
    
    def _calculate_business_priority(self, event: Dict[str, Any]) -> int:
        """Calculate business priority score (1-10)"""
        priority = 5  # Base priority
        
        if event.get('is_priority'):
            priority += 2
        
        if event.get('quality_score', 0) >= 8:
            priority += 1
        
        if event.get('days_until_event', 0) <= 7:
            priority += 1
        
        return min(priority, 10)


# Example usage
if __name__ == "__main__":
    # Sample validated events
    sample_events = [
        {
            'title': 'The Great Jack O\'Lantern Blaze',
            'date': 'Now Through Nov 16, 2025',
            'location': 'Hudson Valley, Croton on Hudson',
            'description': 'Halloween event with thousands of carved pumpkins',
            'url': 'https://www.iloveny.com/event/great-jack-olantern-blaze'
        }
    ]
    
    # Initialize transformer
    transformer = EventTransformer()
    
    # Run transformation pipeline
    result = transformer.transform_events(sample_events)
    
    # Export results
    export_paths = transformer.export_events(result, formats=['json', 'csv'])
    
    print(f"✅ Transformed {len(result['transformed_events'])} events")
    print(f"📊 Success rate: {result['transformation_metadata']['success_rate']:.1f}%")
    print(f"📁 Exported to: {export_paths}")
