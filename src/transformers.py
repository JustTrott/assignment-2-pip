#!/usr/bin/env python3
"""
Event Data Transformation Pipeline
Transforms validated event data for export and analysis
"""

import json
import csv
import re
from datetime import datetime
from typing import List, Dict, Any
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

    def normalize_event_data(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize event data with consistent formatting
        """
        normalized = {}

        # Basic event info
        normalized["title"] = self._clean_text(event.get("title", ""))
        normalized["description"] = self._clean_text(event.get("description", ""))

        # Dates
        normalized["start_date"] = event.get("startDate", "")
        normalized["end_date"] = event.get("endDate", "")
        normalized["date"] = event.get("date", "")

        # Location
        normalized["location"] = event.get("location", "")
        normalized["city"] = event.get("city", "")
        normalized["address"] = event.get("address1", "")

        # URLs
        normalized["event_url"] = event.get("linkUrl", "")

        # Categories from the actual data structure
        categories = event.get("categories", [])
        normalized["categories"] = [cat.get("catName", "") for cat in categories]

        # Additional metadata
        normalized["featured"] = event.get("featured", False)
        normalized["type_name"] = event.get("typeName", "")
        normalized["processed_at"] = datetime.now().isoformat()

        return normalized

    def enrich_event_data(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich event data with additional computed fields
        """
        enriched = event.copy()

        # Add timing metadata
        enriched["days_until_event"] = self._calculate_days_until_event(event)
        enriched["is_upcoming"] = enriched["days_until_event"] >= 0

        # Add location metadata
        enriched["borough"] = self._identify_borough(event)
        enriched["region"] = self._get_region(event)

        # Add content analysis
        enriched["description_length"] = len(event.get("description", ""))
        enriched["has_image"] = bool(event.get("media_raw", []))

        # Add quality score
        enriched["quality_score"] = self._calculate_quality_score(event)

        return enriched

    def calculate_business_metrics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate basic metrics from transformed events
        """
        if not events:
            return {}

        return {
            "total_events": len(events),
            "featured_events": len([e for e in events if e.get("featured", False)]),
            "location_distribution": self._calculate_location_distribution(events),
            "category_distribution": self._calculate_category_distribution(events),
            "average_quality_score": sum(e.get("quality_score", 0) for e in events) / len(events),
        }

    def categorize_event(self, event: Dict[str, Any]) -> str:
        """
        Categorize event using actual categories from data
        """
        categories = event.get("categories", [])
        if categories:
            # Return the first category name
            return categories[0]

        # Fallback to typeName if no categories
        return event.get("type_name", "General")

    def format_for_export(self, event: Dict[str, Any], export_format: str = "standard") -> Dict[str, Any]:
        """
        Format event for export
        """
        if export_format == "minimal":
            return {
                "title": event.get("title", ""),
                "date": event.get("start_date", ""),
                "location": event.get("location", ""),
                "category": event.get("primary_category", ""),
                "url": event.get("event_url", ""),
            }
        else:  # standard format
            return {
                "title": event.get("title", ""),
                "description": event.get("description", ""),
                "start_date": event.get("start_date", ""),
                "end_date": event.get("end_date", ""),
                "location": event.get("location", ""),
                "city": event.get("city", ""),
                "address": event.get("address", ""),
                "borough": event.get("borough", ""),
                "region": event.get("region", ""),
                "primary_category": event.get("primary_category", ""),
                "all_categories": event.get("categories", []),
                "event_url": event.get("event_url", ""),
                "featured": event.get("featured", False),
                "quality_score": event.get("quality_score", 0),
                "days_until_event": event.get("days_until_event", 0),
                "processed_at": event.get("processed_at", ""),
            }

    def apply_business_rules(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply simple business rules to events
        """
        processed_event = event.copy()

        # Mark as priority if featured
        processed_event["is_priority"] = event.get("featured", False)

        # Include in export by default
        processed_event["include_in_export"] = True

        return processed_event

    def transform_events(
        self, validated_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
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
                enriched["primary_category"] = self.categorize_event(enriched)

                # Step 4: Apply business rules
                processed = self.apply_business_rules(enriched)

                # Step 5: Add unique ID
                processed["event_id"] = f"event_{i + 1:05d}_{hash(processed['title']) % 10000:04d}"

                if processed.get("include_in_export", True):
                    transformed_events.append(processed)
                else:
                    skipped_events.append(processed)

            except Exception as e:
                logger.warning(f"Error transforming event {i}: {e}")
                skipped_events.append(
                    {"original_event": event, "error": str(e), "index": i}
                )

        # Calculate business metrics
        business_metrics = self.calculate_business_metrics(transformed_events)

        transformation_result = {
            "transformed_events": transformed_events,
            "skipped_events": skipped_events,
            "business_metrics": business_metrics,
            "transformation_metadata": {
                "total_input_events": len(validated_events),
                "successfully_transformed": len(transformed_events),
                "skipped_events": len(skipped_events),
                "transformation_timestamp": datetime.now().isoformat(),
                "success_rate": (
                    len(transformed_events) / len(validated_events) * 100
                    if validated_events
                    else 0
                ),
            },
        }

        logger.info(
            f"Transformation complete: {len(transformed_events)}/{len(validated_events)} events processed"
        )

        return transformation_result

    def export_events(
        self,
        transformation_result: Dict[str, Any],
        formats: List[str] = None,
        export_format: str = "standard",
    ) -> Dict[str, str]:
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
            formats = ["json", "csv"]

        events = transformation_result["transformed_events"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_paths = {}

        # Format events for export
        formatted_events = [
            self.format_for_export(event, export_format) for event in events
        ]

        # JSON export
        if "json" in formats:
            json_path = self.output_dir / f"transformed_events_{timestamp}.json"
            export_data = {
                "events": formatted_events,
                "metadata": transformation_result["transformation_metadata"],
                "business_metrics": transformation_result["business_metrics"],
            }

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            export_paths["json"] = str(json_path)
            logger.info(f"JSON export saved to: {json_path}")

        # CSV export
        if "csv" in formats and formatted_events:
            csv_path = self.output_dir / f"transformed_events_{timestamp}.csv"

            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=formatted_events[0].keys())
                writer.writeheader()
                writer.writerows(formatted_events)

            export_paths["csv"] = str(csv_path)
            logger.info(f"CSV export saved to: {csv_path}")

        # Business metrics export
        if "metrics" in formats:
            metrics_path = self.output_dir / f"business_metrics_{timestamp}.json"

            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(
                    transformation_result["business_metrics"], f, indent=2, default=str
                )

            export_paths["metrics"] = str(metrics_path)
            logger.info(f"Metrics export saved to: {metrics_path}")

        return export_paths

    # Helper methods
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text.strip())
        return text

    def _calculate_days_until_event(self, event: Dict[str, Any]) -> int:
        """Calculate days until event starts"""
        try:
            start_date_str = event.get("startDate", "")
            if start_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
                return (start_date.date() - datetime.now().date()).days
        except (ValueError, AttributeError):
            pass
        return 0

    def _identify_borough(self, event: Dict[str, Any]) -> str:
        """Identify NYC borough from event data"""
        city = event.get("city", "").lower()
        location = event.get("location", "").lower()

        # Check city field
        if "manhattan" in city or "new york" in city:
            return "Manhattan"
        elif "brooklyn" in city:
            return "Brooklyn"
        elif "queens" in city:
            return "Queens"
        elif "bronx" in city:
            return "Bronx"
        elif "staten island" in city:
            return "Staten Island"

        # Check location field
        if any(borough in location for borough in ["manhattan", "midtown", "downtown", "soho", "tribeca"]):
            return "Manhattan"
        elif any(borough in location for borough in ["brooklyn", "williamsburg", "dumbo"]):
            return "Brooklyn"

        return "Other"

    def _get_region(self, event: Dict[str, Any]) -> str:
        """Get region from udfs_object"""
        udfs = event.get("udfs_object", {})
        for field_id, field_data in udfs.items():
            if isinstance(field_data, dict) and field_data.get("name") == "Regions":
                return field_data.get("value", "")
        return ""

    def _calculate_quality_score(self, event: Dict[str, Any]) -> float:
        """Calculate simple quality score for event"""
        score = 0.0

        # Title quality
        if event.get("title"):
            score += 2.0

        # Description quality
        desc_len = len(event.get("description", ""))
        if desc_len > 50:
            score += 2.0
        elif desc_len > 0:
            score += 1.0

        # URL presence
        if event.get("event_url"):
            score += 1.0

        # Featured bonus
        if event.get("featured", False):
            score += 1.0

        return min(score, 5.0)

    def _calculate_location_distribution(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate location distribution"""
        locations = {}
        for event in events:
            borough = event.get("borough", "Other")
            locations[borough] = locations.get(borough, 0) + 1
        return locations

    def _calculate_category_distribution(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate category distribution"""
        categories = {}
        for event in events:
            category = event.get("primary_category", "General")
            categories[category] = categories.get(category, 0) + 1
        return categories


# Example usage
if __name__ == "__main__":
    # Sample event matching real data structure
    sample_events = [
        {
            "title": "The Great Jack O'Lantern Blaze",
            "startDate": "2025-09-12T04:00:00.000Z",
            "endDate": "2025-11-17T04:59:59.000Z",
            "location": "Van Cortlandt Manor",
            "city": "Croton on Hudson",
            "description": "Halloween event with thousands of carved pumpkins",
            "linkUrl": "https://hudsonvalley.org/events/blaze",
            "featured": True,
            "categories": [{"catName": "Halloween", "catId": "87"}],
        }
    ]

    # Initialize transformer
    transformer = EventTransformer()

    # Run transformation pipeline
    result = transformer.transform_events(sample_events)

    # Export results
    export_paths = transformer.export_events(result, formats=["json", "csv"])

    print(f"✅ Transformed {len(result['transformed_events'])} events")
    print(f"📊 Success rate: {result['transformation_metadata']['success_rate']:.1f}%")
    print(f"📁 Exported to: {export_paths}")
