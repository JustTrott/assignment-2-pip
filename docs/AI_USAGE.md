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

### Main Scraper Logic
**Date**: Current session
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
