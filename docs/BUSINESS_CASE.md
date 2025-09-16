# Business Case
## Data Opportunity Brief: NYC Activity Planning Data

### Problem Statement & Market Size
Planning activities in New York City is overwhelming—tourists and locals face fragmented sources for events, attractions, and hidden gems. The U.S. travel & tourism market was valued at $2.3 trillion in 2023, with NYC tourism alone contributing $74 billion annually. Yet consumers still lack a consolidated, personalized dataset to streamline decision-making. A structured feed of NYC activities, events, and attractions from iloveny.com would help millions of users navigate the city efficiently.

### Why This Data Isn’t Readily Available
While APIs exist for event discovery (e.g., Ticketmaster, Yelp, Google Places), they are:\
**Expensive**: Many charge per-call fees that scale poorly for consumer apps.\
**Clunky**: Results are generic, missing context like local tourism curation.\
**Fragmented**: APIs cover only concerts, restaurants, or ticketed events—not the full mix of cultural, seasonal, and free activities.\
**Inconsistent**: Data quality varies (duplicate events, incomplete listings, outdated entries).
iloveny.com offers curated, official, and trustworthy content, but lacks a modern API for easy integration into consumer-facing planning tools.

### Potential Users & Willingness to Pay
**Tourists**: Willing to pay for convenience and time-saving itineraries. (NYC visitors spend an average of $2,000 per trip—a $10–$30 trip-planning app upsell is feasible.)\
**Local Experience-Seekers**: Residents looking for new activities (subscription models: $5–$15/month).\
**Travel Agencies & Concierge Services**: High willingness to pay for bulk licensing of curated activity data.\
**Hospitality Sector (hotels, Airbnbs, tour operators)**: Could integrate the feed to upsell packages.\
Generative AI–based personalization increases perceived value, making data-driven planning apps “sticky.”

### Competitive Landscape
Yelp / Google Maps / TripAdvisor: Broad but cluttered, prioritizing sponsored content. Limited personalization.\
Eventbrite / Ticketmaster: Strong for paid events but not for free attractions or cultural guides.\
Time Out NYC: Editorial-driven, not API-friendly, hard to automate at scale.\
NYCGo.com (NYC’s official guide): Overlaps with iloveny.com but also lacks API accessibility.\
Opportunity: Position as the trusted, structured, API-accessible dataset for NYC activities. Differentiation comes from curated, tourism-first content that blends official events + local gems + seasonal highlights, packaged in a developer-friendly way.

## [Slide Deck](https://docs.google.com/presentation/d/10_y8_etz0asrHSKl-7XrajIx8a8AwMXBkYJdWUqhzKo/edit?usp=sharing)

### Main Points:
**Problems and Market Opportunities:**\
*Overwhelming Process:* With the wide variety of activities to do in NYC, people can experience decision fatigue when trying to make plans for their city trips.\
*Lack of Accessibility:* Most trip planners don't focus on the reasonable things for customers to do. Whether the plans involve long travel distances within the city or spending beyond an intended budget, a poor plan subtracts from the experience of the city.\
*Limited Personalization:* Again, there are so many options available to users, just not ones that are specifically catered to them.\
*Market Opportunity:* The NYC tourism industry earns **$74 billion** annually, yet there doesn't exist a model that is able to streamline the process of planning a trip to NYC. On average, tourists spend about **$2,000** per trip, justifying an additional cost to use a simple service to help them plan their trip, it would definitely save them a great pain.

**Technical Solution:**\
*- Scrape Data:* Using the iloveny.com website, we can scrape the site for events that are currently posted and compile the data in one location that it can be easily accessed from. This data will be loaded to the app after undergoing validation and transformation so that it can be used to help plan activities.\
*- Implement User Input:* Upon the launch of the app, users will be prompted to input the types of activities they are interested in looking for during that session. Within the app settings, users can control how long that preference is set for so they aren’t repeatedly prompted every time they open the app.\
*- Implement Location Services:* Events will be featured by distance in accordance to other events being planned within the app. A  map will show proximity between activities, and commute options will be detailed if needed.

**Pricing Model:**

**Subscription Plan**\
*Tier 1:* Free (Freemium Hook)\
Limited access (e.g., view up to 3 curated itineraries, no personalization).
Ads displayed (local attractions, restaurants, tours).\
Purpose: Funnel users into paid tiers.\
*Tier 2:* Traveler Plan – $9.99/month\
Unlimited itineraries with AI personalization (interests, budget, time).\
Real-time event updates + seasonal recommendations.\
Save & share itineraries with travel companions.\
Offline access (download city maps + itinerary).\
*Tier 3:* Explorer Plan – $14.99/month\
Includes Traveler Plan features plus:\
Premium concierge tools (restaurant + event booking integrations).\
Exclusive discounts (affiliate partnerships with tours, events).\
Multi-city support (NYC, then expand to other cities later).

**Single-Use**\
*Option A:* 24-Hour Pass – $4.99\
Full feature unlock for 24 hours.\
Good for last-minute planners who just need a quick itinerary.\
*Option B:* Trip Pass – $14.99 (per trip, up to 14 days)\
Full access to all premium features during a single trip.\
Includes offline access + personalized itinerary builder.\
Competitive with hiring a tour guide or concierge, but much cheaper.
