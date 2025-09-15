# AI Usage Documentation

## Project Team
- **Temirlan**
- **Veyd**

## AI Collaboration Tools
- **Super Whisper**: Used by Temirlan for voice-to-text transcription
- **Cursor AI**: Used by Temirlan for code assistance and project setup
- **Claude AI**: Used by Veyd for code assistance

## Prompt History

### Initial Setup (Temirlan)
**Date**: 9/14
**Prompt**: 
```
NOTE: You MUST follow this repository structure - we have an automated tool to assist us with grading, which will fail if you don't follow it.

project-name/
├── src/
│   ├── scraper.py          # Main scraping logic
│   ├── validators.py       # Data validation rules
│   ├── transformers.py     # Data transformation pipeline
├── docs/
│   ├── BUSINESS_CASE.md    # Market analysis and pricing
│   ├── ETHICS.md           # Detailed ethical analysis
│   ├── ARCHITECTURE.md     # Technical design decisions
│   ├── AI_USAGE.md         # AI collaboration documentation
├── data/
│   └── sample_output.json  # Example of processed data
├── requirements.txt
├── README.md
└── .gitignore

I want you to set up this project structure and also log every prompt that I sent you to the AI usage MD. And also create a cursor rule for that
For now, do not fill the text in the markdown files, and you do not need to write any code, just create the files.
Well, except for AI usage. And can you also write in the AI usage that I'm using an application called Super Whisper to transcribe whatever I'm saying. Also, there are two people working on this project. I am Temirlan, and there will be another person Veyd. This doesn't relate to him, he may use other technologies.
```
**AI Response**: Set up complete project structure with all required directories and files, created AI_USAGE.md with initial documentation including team information and Super Whisper usage. 

### Main Scraper Logic (Veyd)
**Date**: 9/14
**Prompt**:
```
can you write a web scraper, scraper.py, for iloveny.com/events using beautiful soup and the strategy in the pre-implementation doc below:
**Scraping Strategy Document: **
**iloveny.com/events**
**1. Data Collection Priorities**
* **Event Core Info (Highest Priority)**
   * Title, date(s), location, category, description, URL.
   * These are essential for identifying and indexing events.
* **Secondary Metadata**
   * Images, ticket details (if present), region, organizer.
   * Useful for enrichment but not mandatory for baseline functionality.
* **Filters/Tags**
   * Capture category labels (e.g., Music, Sports) and region filters.
   * Helps with search and segmentation in later analysis.
**Why this order? **Event core info provides the minimum viable dataset. Metadata and filters enhance usability but can be added later.
**2. Fallback Strategies for Common Failures**
**Failure Mode → Strategy**
* **Site structure changes (HTML layout breaks selectors): **→ Maintain modular scraper code with CSS/XPath selectors stored in configs for quick updates.
* **Rate limiting / blocking (HTTP 429 or captcha): **→ Use rotating residential proxies, polite crawl rates (2–5 seconds between requests), and header randomization.
* **Content hidden behind JavaScript rendering: **→ Deploy headless browser scraping (e.g., Puppeteer, Playwright) as fallback when static HTML scraping fails.
* **Missing fields (e.g., no end date on an event): **→ Fill with default values (“TBD”), log issue, and flag for human QA if persistent.
* **Dead links / 404s: **→ Maintain link validation checkers; auto-remove broken URLs after 2 failed retrievals.
**3. Data Quality Validation Rules**
* **Event Dates:** Must be valid future dates; reject past-dated events unless explicitly “historical archive.”
* **Locations:** Must include a valid NYC borough or recognizable address; use geocoding API to standardize.
* **Duplicates:** Compare normalized event name + date + venue; flag and consolidate duplicates.
* **Categorization:** Map scraped categories to internal taxonomy (e.g., “music festival” → Music > Festivals).
* **Links & Images:** Ensure event URL resolves (HTTP 200) and image URLs return valid file types.
* **Text Cleanliness:** Strip HTML artifacts, normalize whitespace, handle Unicode encoding issues.
**4. Update Frequency & Justification**
* **Events & Activities:** **Daily updates**
   * Justification: Event calendars change rapidly; cancellations, new listings, and venue updates occur daily.
* **Attractions & Landmarks:** **Monthly updates**
   * Justification: Museums, parks, and permanent attractions rarely change.
* **Seasonal Guides & Editorial Features:** **Quarterly updates**
   * Justification: Aligned with tourism cycles (spring, summer, fall, winter).
* **Blog Posts / Insider Tips:** **Weekly updates**
   * Justification: Medium-paced publishing schedule; weekly crawl balances freshness and efficiency.
* **Partner Offers / Deals:** **Daily updates**
   * Justification: Deals expire quickly; must refresh daily to prevent stale content.

Include rules for respectful scraping like exponential backoff and a retry limit. Export the results in a single format (CSV/JSON) or output to a folder.
```
**AI Response**: Generated skeleton for web scraper and output key features included.

### Architecture Documentation and Scraper Implementation (Temirlan)
**Date**: 9/14
**Prompt**:
```
We will create a iloveny.com/events scraper, first i want you to document the current architecture in the @ARCHITECTURE.md 

We tried scraping using bs4, but the website is dynamic, so we decided to reverse engineer the API

remember this
Your scraper should demonstrate these concepts:
# 1. Data Quality Assurance
- Validation rules for scraped data
# 2. Respectful Scraping
- Implement exponential backoff 
- Retry limit
# 3. Business Logic
- Data transformation pipeline, even if very basic (we'll cover data transformation in more detail later, for now, just ask the LLM to help you with transformation)
- Value-added calculations or insights
- Export in a single format (CSV, JSON) or output to a folder (e.g., /images)

The important requests are

curl 'https://www.iloveny.com/plugins/core/get_simple_token/'

which gets the auth token

and

curl 'https://www.iloveny.com/includes/rest_v2/plugins_events_events_by_date/find/?json=%7B%22filter%22%3A%7B%22solrOptions%22%3A%7B%7D%2C%22primary_site%22%3A%22primary%22%2C%22categories.catId%22%3A%7B%22%24in%22%3A%5B%223%22%2C%225%22%2C%226%22%2C%22106%22%2C%2274%22%2C%2297%22%2C%2231%22%2C%22100%22%2C%2210%22%2C%22101%22%2C%22102%22%2C%2287%22%2C%2229%22%2C%2211%22%2C%2212%22%2C%2214%22%2C%2215%22%2C%22113%22%2C%2218%22%2C%2298%22%2C%2299%22%2C%22111%22%2C%2226%22%2C%2230%22%5D%7D%2C%22date_range%22%3A%7B%22start%22%3A%7B%22%24date%22%3A%222025-09-18T04%3A00%3A00.000Z%22%7D%2C%22end%22%3A%7B%22%24date%22%3A%222025-09-26T04%3A00%3A00.000Z%22%7D%7D%7D%2C%22options%22%3A%7B%22skip%22%3A0%2C%22limit%22%3A12%2C%22hooks%22%3A%5B%22afterFind_listing%22%2C%22afterFind_host%22%5D%2C%22sort%22%3A%7B%22featured%22%3A-1%2C%22date%22%3A1%2C%22rank%22%3A1%2C%22title%22%3A1%7D%2C%22fields%22%3A%7B%22accountId%22%3A1%2C%22categories%22%3A1%2C%22detailURL%22%3A1%2C%22featured%22%3A1%2C%22host_id%22%3A1%2C%22host.recid%22%3A1%2C%22host.title%22%3A1%2C%22host.detailURL%22%3A1%2C%22latitude%22%3A1%2C%22listing%22%3A1%2C%22listing_id%22%3A1%2C%22listing.recid%22%3A1%2C%22listing.title%22%3A1%2C%22listing.detailURL%22%3A1%2C%22listing.region%22%3A1%2C%22address1%22%3A1%2C%22location%22%3A1%2C%22longitude%22%3A1%2C%22media_raw%22%3A1%2C%22nextDate%22%3A1%2C%22primary_site%22%3A1%2C%22rank%22%3A1%2C%22recId%22%3A1%2C%22recid%22%3A1%2C%22recurType%22%3A1%2C%22recurrence%22%3A1%2C%22startDate%22%3A1%2C%22endDate%22%3A1%2C%22startTime%22%3A1%2C%22endTime%22%3A1%2C%22title%22%3A1%2C%22description%22%3A1%2C%22typeName%22%3A1%2C%22loc%22%3A1%2C%22url%22%3A1%2C%22date%22%3A1%2C%22city%22%3A1%2C%22udfs_object%22%3A1%2C%22ticketmaster%22%3A1%2C%22linkUrl%22%3A1%2C%22hostname%22%3A1%7D%2C%22count%22%3Atrue%7D%7D&token=4bd5143fc1bf1403064ebc415e88546a'

it's a sample requests that the main page sends to get the events data

for now, the @validators.py and @transformers.py should not be implemented, the other dev will do them, you should implement the @scraper.py 

The requirements above were for entire application, so keep it in mind. you can create placeholder methods for validation and transformation if need be.
```

**AI Response**: Documented comprehensive architecture in ARCHITECTURE.md explaining the API reverse engineering approach, implemented complete scraper.py with authentication, exponential backoff, retry logic, and data export functionality, added placeholder methods to validators.py and transformers.py for future implementation by Veyd, and updated requirements.txt with necessary dependencies.

### Validation and Transformer Implementation (Veyd)
**Date**: Current session
**Prompt**:
```
We reverse engineered the API for Iloveny but now we want to validate the data with the following functions only:
validate_event_date - validate for date in future (argument: event dictionary, return: boolean)
validate_location - validate for located in NYC (argument: event dictionary, return: boolean)
detect_duplicates - detect and flag duplicate events (argument: list of event dictionaries, return: list of duplicate events)
validate_data_completeness - check for completeness in title, date, location, and description (argument: event dictionary, return: string and boolean dictionary for the required fields)
validate_links - validate for accessible URLs (argument: event dictionary, return: boolean)
normalize_text - normalize text by cleaning HTML artifacts and whitespace (argument: raw text, return: normalized text)
validate_events - main validation function for list of events (argument: list of event dictionaries, return: validation results dictionary containing (total events, valid events, invalid events, duplicates, validation errors)
```
**AI Response**: Implemented validation functions, including an extra function called ```calculate_text_similarity``` which was deleted.

**Prompt**:
```
we are also looking for a basic data transformation pipeline
the functions that exist in the class skeleton are:
normalize_event_data
enrich_event_data
calculate_business_metrics
categorize_event
format_for_export
apply_business_rules
transform_events
export_events
```
**AI Response**: Implemented data transformation functions extensively. Need to review decisions later and connect all of the work together.
