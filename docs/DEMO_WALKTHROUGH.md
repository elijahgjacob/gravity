# Gravity Frontend Demo Walkthrough

This guide provides a step-by-step walkthrough of the Gravity ad retrieval system frontend, demonstrating user profiling, query retrieval, and system monitoring features.

---

## 🎯 Demo Flow Overview

1. **Set User IP Address** → Establish user identity
2. **Send First Query** → Create initial user profile
3. **Send Additional Queries** → Build query history and patterns
4. **View User Profile** → Inspect accumulated profile data
5. **Inspect Request/Response** → Examine API payloads

---

## Step 1: Set User IP Address

### Location
At the top of the page, look for the **"User Profile & Journey"** card (light blue header).

### Actions

1. **Locate the IP Address input**
   - Find the section labeled "Set user context (optional)"
   - You'll see two input fields: **"IP Address"** and **"Device ID (optional)"**

2. **Enter a User IP Address**
   - Type a sample IP address (e.g., `192.168.1.100`)
   - The system uses this to create a unique user identifier

3. **Optional: Add Device ID**
   - For more precise tracking, add a device identifier (e.g., `mobile-123`)
   - This helps differentiate multiple devices from the same IP

4. **Click "Set User"**
   - This activates user tracking for subsequent queries
   - A blue badge will appear showing "Active user: ip_192.168.1.100"

### What to Notice
- The **user_id** is automatically derived from IP and device ID
- Format: `ip_<sanitized_ip>_dev_<sanitized_device>` (if both provided)
- This user_id will be attached to all future queries

---

## Step 2: Send Your First Query

### Location
Scroll down to the **"Search Query"** card.

### Actions

1. **Enter a Query**
   - Type a search query in the large input field (e.g., `running shoes for marathon`)
   - Or click one of the example queries:
     - "best running shoes for marathon"
     - "affordable laptop for students"
     - "luxury watches for men"
     - "organic dog food delivery"
     - "yoga classes near me"

2. **Optional: Add User Context**
   - Click **"Add User Context"** to expand additional fields
   - Fill in demographic information:
     - **Age**: e.g., `28`
     - **Gender**: Select from dropdown (male, female, non-binary, other)
     - **Location**: e.g., `San Francisco, CA`
     - **Interests**: Comma-separated (e.g., `fitness, health, marathons`)
   - This context enriches the user profile

3. **Click "Search" button**
   - Wait for the system to process (typically 50-100ms)
   - The button will show a loading spinner

### What to Notice

**Server Status (Top Right)**
- Watch the badge change from "Warming..." to "Ready" (green dot)
- System stats: "10k" campaigns, "<100ms" target latency, "384D" embeddings

**Results Appear**
- Below the search box, you'll see campaign cards appear
- Each card shows:
  - Campaign title
  - Description
  - Category badge (e.g., "Sports & Fitness")
  - Similarity score (e.g., "94.5%")

**Metrics Panel (Right Sidebar)**
- **Latency**: Total retrieval time (e.g., "76.4 ms")
- **Campaigns Retrieved**: Number of results (e.g., "1000")
- **Retrieval Method**: Shows "FAISS Vector Search"
- **Top Category**: Most common category in results

---

## Step 3: Send Additional Queries

### Actions

1. **Send a Related Query**
   - Try: `marathon training gear`
   - Click Search again

2. **Send a Different Category Query**
   - Try: `wireless headphones for running`
   - This helps build a diverse interest profile

3. **Send More Queries (Recommended: 5-10 total)**
   - Example progression:
     1. `running shoes for marathon` ← Sports
     2. `protein powder for athletes` ← Sports/Health
     3. `fitness tracker watch` ← Sports/Tech
     4. `yoga mat and blocks` ← Sports/Wellness
     5. `healthy meal prep containers` ← Health/Lifestyle
     6. `running shorts men` ← Sports/Apparel
     7. `sports water bottle` ← Sports/Accessories

### What to Notice

**Each Query:**
- Creates a new entry in the user's query history (when profile tracking enabled)
- Updates the profile's inferred intents and categories
- Contributes to pattern detection (e.g., "Sports & Fitness Enthusiast")
- Triggers profile analysis after every 5th query (when `PROFILE_ANALYSIS_ENABLED=true`)

**Results Change:**
- Campaigns match the query semantically
- Similarity scores reflect query-campaign relevance
- Categories shift based on query domain

---

## Step 4: View User Profile & Journey

### Location
Return to the **"User Profile & Journey"** card at the top.

### Actions

1. **Load Your User Profile**
   
   **Option A: From Manual Input**
   - Under "Demo: Manual user_id input", paste your user_id
   - Format: `ip_192.168.1.100` (or whatever you set)
   - Click "Load Profile"
   
   **Option B: From Cache**
   - Click the dropdown under "From cache:"
   - Select your user from the list (shows query count)
   - Click "Load Profile"

2. **Expand the Profile Details**
   - Look for the blue card that appears with your user_id
   - Click the **"Profile Details"** header (with the down arrow)
   - The accordion will expand to show full details

### What to See (Inside the Expanded Accordion)

**📊 Profile Metadata**
- **User ID**: Your assigned identifier (e.g., `ip_192.168.1.100`)
- **Query Count**: Number of queries sent (e.g., "7 queries")
- **Last Updated**: Timestamp of most recent activity

**🔍 Recent Queries**
- Complete list of your search queries in reverse chronological order
- Maximum 15 most recent queries shown
- Example:
  ```
  1. sports water bottle
  2. running shorts men
  3. healthy meal prep containers
  4. yoga mat and blocks
  ...
  ```

**🎯 Inferred Intents**
- Pattern-based intent detection results
- Each intent shows:
  - **Intent Type**: e.g., "Sports & Fitness Enthusiast"
  - **Confidence**: e.g., "85%"
  - **Metadata**: Supporting evidence (keyword patterns, query frequency)
  - **Inferred Categories**: Detected from queries (e.g., "Sports", "Health")

**🏷️ Categories & Interests**
- **Inferred Categories** (purple badges): System-detected from queries
- **Aggregated Interests** (indigo badges): Consolidated from context

**🤖 LLM Summary** (When Profile Analysis Enabled)
- **Narrative Summary**: AI-generated profile description
  - Example: "User demonstrates strong interest in fitness and athletic activities, with focus on running and marathon training. Queries suggest health-conscious lifestyle with emphasis on quality athletic gear."
- **Suggested Ad Campaigns**: LLM recommendations
  - Example campaigns tailored to detected interests
  - "→ Premium running shoes for serious athletes"
  - "→ Marathon training nutrition plans"

**Special Cases:**
- If summary shows "Summary not available":
  - Profile analysis may be disabled (`PROFILE_ANALYSIS_ENABLED=false`)
  - Or OpenRouter API key may not be configured
- Pattern-based analysis still works without LLM when profile analysis is enabled
- **Production Note**: Profile analysis is disabled by default for latency optimization

3. **Trigger Manual Analysis**
   - Click **"Force Analyze"** button to re-run profile analysis
   - Shows loading spinner "Analyzing..."
   - Updates the summary with latest query data

4. **Refresh the Profile**
   - Click the **refresh icon** (🔄) next to "Load Profile"
   - Re-fetches latest profile data from the server

---

## Step 5: Inspect Request & Response

### Location
Scroll to the bottom of the page, below the results section.

### Component: "Request & Response Inspector"

### Actions

1. **Expand the Inspector**
   - Look for the card labeled **"Request & Response Inspector"**
   - If collapsed, click to expand

2. **View the Request**
   - Click the **"Request"** tab (blue/indigo)
   - You'll see the JSON payload sent to the API:
   
   ```json
   {
     "query": "running shoes for marathon",
     "user_id": "ip_192.168.1.100",
     "context": {
       "age": 28,
       "gender": "male",
       "location": "San Francisco, CA",
       "interests": ["fitness", "health", "marathons"]
     }
   }
   ```

3. **View the Response**
   - Click the **"Response"** tab
   - You'll see the full API response:
   
   ```json
   {
     "query": "running shoes for marathon",
     "campaigns": [
       {
         "campaign_id": "CAMP_1234",
         "title": "Premium Marathon Running Shoes",
         "description": "Professional-grade running shoes...",
         "category": "Sports & Fitness",
         "score": 0.9453
       },
       // ... 999 more campaigns
     ],
     "metadata": {
       "total_candidates": 1000,
       "retrieval_method": "FAISS Vector Search",
       "filters_applied": [],
       "top_category": "Sports & Fitness"
     },
     "latency_ms": 76.43,
     "timestamp": "2026-02-25T01:49:11.123456"
   }
   ```

4. **Copy JSON Data**
   - Click **"Copy Request"** or **"Copy Response"** buttons
   - Use for debugging, testing, or documentation

### What to Notice

**Request Structure:**
- `query`: Your search text
- `user_id`: Automatically attached from user context
- `context`: Optional demographic data (if provided)

**Response Structure:**
- `campaigns`: Array of retrieved ad campaigns (up to 1000)
- `metadata`: System statistics and retrieval info
- `latency_ms`: Server-side processing time
- `timestamp`: When the query was processed

**Response Size:**
- Campaigns array can be very large (1000 items)
- The JSON viewer provides scrolling for large payloads
- Notice the syntax highlighting for readability

---

## 🎨 Additional UI Features

### Theme Toggle
- **Location**: Top right corner (sun/moon icon)
- **Action**: Click to switch between light and dark mode
- **Persistence**: Theme preference is saved in browser

### Metrics Panel (Right Sidebar)

Shows real-time system metrics:
- **Latency**: How fast the query was processed
- **Campaigns**: Number of results returned
- **Method**: Retrieval algorithm used (FAISS)
- **Top Category**: Most common category in results

### Results Display

Each campaign card shows:
- **Title & Description**: Campaign content
- **Category Badge**: Product/service category
- **Similarity Score**: How well it matches your query (%)
- **Click**: Future feature for campaign interaction

---

## 🧪 Demo Scenarios

### Scenario 1: Fitness Enthusiast Profile
```
1. Set IP: 192.168.1.100
2. Queries:
   - "running shoes for marathon"
   - "protein supplements for athletes"
   - "fitness tracker watch"
   - "gym membership deals"
   - "yoga mat"
3. Check Profile → Should show "Sports & Fitness Enthusiast"
```

### Scenario 2: Tech Shopper Profile
```
1. Set IP: 192.168.1.101
2. Queries:
   - "best laptop for programming"
   - "mechanical keyboard"
   - "4k monitor for coding"
   - "wireless mouse"
   - "usb-c hub"
3. Check Profile → Should show technology/electronics categories
```

### Scenario 3: Parent Profile
```
1. Set IP: 192.168.1.102
2. Queries:
   - "organic baby food"
   - "car seat for toddler"
   - "educational toys age 3"
   - "baby monitor with camera"
   - "kids books age 5"
3. Check Profile → Should show parenting/children categories
```

---

## 🔍 What Makes This Interesting

### Real-Time Profiling
- Every query updates the user profile instantly
- Pattern detection runs automatically
- No need to refresh or wait for batch processing

### Privacy-Preserving
- User identifiers are ephemeral (IP-based)
- No permanent storage of PII
- In-memory caching with TTL (7 days default)

### Semantic Search
- Results are based on meaning, not just keywords
- Try: "footwear for long distance running" → Still returns marathon shoes
- 384-dimensional embeddings capture semantic similarity

### Optimized Latency
- FAISS index enables fast vector search
- Pre-loaded embeddings and models
- Graphiti and Profile Analysis disabled in production for speed
- Embedding cache for repeated queries

---

## 🐛 Troubleshooting

### "No profile yet" Message
- **Cause**: User hasn't made any queries yet
- **Fix**: Send at least one query with that user_id

### LLM Summary Not Available
- **Cause**: OpenRouter API key not configured
- **Impact**: Pattern-based analysis still works
- **Fix**: Admin must set OPENROUTER_API_KEY in environment

### Empty User List in Dropdown
- **Cause**: No users have made queries yet
- **Fix**: Create profiles by sending queries

### Slow First Query
- **Cause**: Server cold start (Railway.app) - embedding model loading
- **Wait**: Server shows "Warming..." then "Ready"
- **Impact**: First query may take 1-3 seconds, subsequent queries faster
- **Tip**: Call `/api/warmup` endpoint to pre-warm the server

### Profile Features Not Working
- **Cause**: Profile analysis disabled in production for latency
- **Check**: `PROFILE_ANALYSIS_ENABLED` environment variable
- **Impact**: User profiles still tracked, but LLM summaries unavailable

---

## 📝 Notes for Demonstrators

1. **Start with a clear IP**: Use memorable IPs like `192.168.1.100` for easy reference
2. **Tell a story**: Build queries around a persona (fitness, tech, parenting)
3. **Show the journey**: Demonstrate how profile evolves with more queries
4. **Highlight speed**: Point out the <100ms latency in the metrics panel
5. **Explain semantic search**: Show how similar queries return similar results
6. **Demo the LLM**: If available, show how AI summarizes the user profile

---

## 🚀 Advanced Features

### Profile Analysis (Optional)
- LLM analysis runs every 5th query when enabled
- Can be forced with "Force Analyze" button
- Configurable via `PROFILE_ANALYSIS_TRIGGER_EVERY_N_QUERIES`
- **Note**: Disabled in production (`PROFILE_ANALYSIS_ENABLED=false`) for latency optimization
- User profiles and query history still tracked; only LLM analysis is disabled

### Cache Management
- Profiles cached for 7 days (configurable)
- Maximum 10,000 profiles in memory
- LRU eviction when cache is full

### Graphiti Integration (Optional)
- Knowledge graph of user journeys
- Temporal analysis of query patterns
- Campaign co-occurrence tracking
- **Note**: Disabled in production (`GRAPHITI_ENABLED=false`) for latency optimization
- Enable for development/testing environments only

---

**Enjoy exploring Gravity! 🚀**
