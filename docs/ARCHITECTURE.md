# Architecture Documentation

## System Overview

The iloveny.com/events scraper is designed to extract event data from the I Love NY website using a reverse-engineered API approach. The system prioritizes data quality, respectful scraping practices, and business value generation.

## Architecture Decision: API Reverse Engineering

### Initial Approach: Beautiful Soup (Failed)
- **Problem**: The website uses dynamic content loading with JavaScript
- **Issue**: Beautiful Soup can only parse static HTML, missing dynamically loaded content
- **Solution**: Reverse engineer the underlying API endpoints

### Current Approach: API Integration
- **Method**: Direct API calls to the website's internal REST endpoints
- **Advantages**: 
  - More reliable than HTML parsing
  - Faster data retrieval
  - Structured JSON responses
  - Less prone to breaking with UI changes

## System Components

### 1. Scraper Module (`src/scraper.py`)
**Purpose**: Main data collection engine
**Responsibilities**:
- Authentication token retrieval
- API endpoint communication
- Data fetching with retry logic
- Error handling and logging

**Key API Endpoints**:
- `GET /plugins/core/get_simple_token/` - Authentication
- `GET /includes/rest_v2/plugins_events_events_by_date/find/` - Event data

### 2. Validators Module (`src/validators.py`)
**Purpose**: Data quality assurance
**Responsibilities**:
- Event date validation
- Location data validation
- Duplicate detection
- Data completeness checks

### 3. Transformers Module (`src/transformers.py`)
**Purpose**: Data transformation pipeline
**Responsibilities**:
- Data normalization
- Business logic application
- Value-added calculations
- Export formatting

## Data Flow

```
1. Authentication → Get token from /get_simple_token/
2. API Request → Query events with filters and date range
3. Raw Data → JSON response from API
4. Validation → Apply data quality rules
5. Transformation → Normalize and enrich data
6. Export → Output to CSV/JSON format
```

## Technical Specifications

### Authentication Strategy
- Token-based authentication
- Token refresh mechanism
- Session management

### Data Collection Strategy
- Date range filtering
- Category filtering (23 predefined categories)
- Pagination support (limit: 12 per request)
- Sorting by featured status, date, rank, and title

### Error Handling
- Exponential backoff for rate limiting
- Retry limits (configurable)
- Graceful degradation
- Comprehensive logging

### Data Quality Assurance
- Future date validation
- Location standardization
- Duplicate detection
- Link validation
- Text normalization

## Business Logic Integration

### Value-Added Features
- Event categorization mapping
- Geographic data enrichment
- Featured event prioritization
- Recurring event handling

### Export Formats
- CSV for tabular analysis
- JSON for API integration
- Structured folder output for media files

## Performance Considerations

### Respectful Scraping
- Configurable request delays
- Exponential backoff on failures
- Rate limiting compliance
- User-agent rotation

### Scalability
- Modular design for easy maintenance
- Configurable batch sizes
- Parallel processing capabilities
- Memory-efficient data handling

## Security & Compliance

### Data Privacy
- No personal information collection
- Public event data only
- Respectful of robots.txt (if applicable)

### Rate Limiting
- Built-in delays between requests
- Automatic retry with backoff
- Request throttling
