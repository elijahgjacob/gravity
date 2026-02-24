# User Profile Inference System

## Overview

The User Profile Inference System dynamically learns from user query patterns to infer intent and personalize ad recommendations. For example, if a user searches for "marathon shoes" → "Boston weather" → "Boston hotels", the system infers marathon participation intent and suggests airfare/travel packages.

## Architecture

```
Query → Profile Lookup (1-2ms) → Retrieval Pipeline → Response
                                        ↓
                                  Profile Update
                                        ↓
                              Background Analysis (every 5th query)
                                        ↓
                              Pattern Detection → Intent Inference
                                        ↓
                              Update Cached Profile
```

## Key Components

### 1. Profile Repository (`src/repositories/profile_repository.py`)
- **In-memory cache** using TTLCache (no external dependencies)
- Stores user profiles with 7-day TTL
- Fast lookups: < 2ms
- Capacity: 10,000 users (configurable)

### 2. Pattern Detector (`src/services/pattern_detector.py`)
- Applies configurable rules to detect intent patterns
- Matches query sequences against pattern definitions
- Calculates confidence scores
- Extracts metadata (locations, dates, etc.)

### 3. Profile Analyzer (`src/services/profile_analyzer.py`)
- Runs asynchronously in background
- Analyzes query history to detect patterns
- Updates user profiles with inferred intents
- Zero impact on retrieval latency

### 4. Pattern Rules (`data/pattern_rules.json`)
- JSON configuration for pattern definitions
- 8 pre-built rules (marathon, vacation, shopping, etc.)
- Easily extensible without code changes

## Configuration

Add to `.env`:

```env
# Profile Analysis
PROFILE_ANALYSIS_ENABLED=true
PROFILE_CACHE_SIZE=10000
PROFILE_CACHE_TTL_SECONDS=604800  # 7 days
PROFILE_ANALYSIS_TRIGGER_EVERY_N_QUERIES=5
PATTERN_RULES_PATH=data/pattern_rules.json
PATTERN_CONFIDENCE_THRESHOLD=0.75
```

## Usage

### 1. Include user_id in requests

```python
import httpx

response = httpx.post("http://localhost:8000/api/retrieve", json={
    "query": "best marathon running shoes",
    "user_id": "user_12345",  # Required for profile tracking
    "session_id": "sess_abc",  # Optional
    "context": {
        "age": 30,
        "gender": "male",
        "location": "San Francisco, CA",
        "interests": ["fitness", "running"]
    }
})
```

### 2. System automatically:
- Creates/updates user profile
- Tracks query history
- Triggers analysis every 5 queries
- Detects patterns
- Infers intent and categories
- Enriches future queries with inferred categories

### 3. Inferred categories boost relevant ads

Query 1-3: Build pattern (shoes → weather → hotels)
Query 4+: Automatically include `airfare`, `travel_packages` categories

## Pattern Rules

### Marathon Planning Rule

```json
{
  "rule_id": "marathon_planning",
  "pattern": [
    {
      "step": 1,
      "keywords": ["marathon", "running", "shoes"],
      "category_match": ["running_shoes"]
    },
    {
      "step": 2,
      "keywords": ["weather", "forecast"],
      "requires_location": true
    },
    {
      "step": 3,
      "keywords": ["hotel", "accommodation"],
      "requires_location": true,
      "location_must_match_step": 2
    }
  ],
  "inferred_categories": ["airfare", "travel_packages", "car_rental"],
  "confidence_threshold": 0.75,
  "time_window_hours": 168
}
```

### Adding Custom Rules

1. Edit `data/pattern_rules.json`
2. Add new rule with pattern steps
3. Restart server (auto-reloads with `--reload` flag)

## Testing

Run the test suite:

```bash
python scripts/test_profile_inference.py
```

This tests:
- Marathon planning scenario
- Vacation planning scenario
- Profile creation and updates
- Pattern detection
- Category inference

## Performance

- **Profile lookup**: < 2ms (in-memory cache)
- **Profile update**: 0ms impact (async)
- **Analysis**: 0ms impact (background)
- **Retrieval latency**: Unchanged (~24ms avg)

## Monitoring

Check profile system status:

```python
# Get dependencies status
response = httpx.get("http://localhost:8000/api/health")
health = response.json()

# Check if profile analysis is enabled
print(health["dependencies"]["profile"])  # True/False
print(health["dependencies"]["profile_analyzer"])  # True/False
```

## How It Works

### Step 1: Query Processing
```python
# User makes query with user_id
POST /api/retrieve
{
  "query": "marathon shoes",
  "user_id": "user_123"
}
```

### Step 2: Profile Lookup (Fast)
```python
# Controller checks for existing profile
inferred_categories = await profile_repo.get_inferred_categories(user_id)
# Returns: [] (no profile yet)
```

### Step 3: Normal Retrieval
```python
# Extract categories from query
extracted = ["running_shoes", "athletic_footwear"]

# Merge with inferred (empty for now)
all_categories = extracted + inferred_categories
# Result: ["running_shoes", "athletic_footwear"]
```

### Step 4: Profile Update (Async)
```python
# Fire-and-forget: Update profile in background
asyncio.create_task(update_profile(user_id, query, categories))

# Profile now has:
# - query_count: 1
# - query_history: ["marathon shoes"]
```

### Step 5: Trigger Analysis (Every 5 Queries)
```python
# After 5th query, trigger analysis
if query_count % 5 == 0:
    asyncio.create_task(analyze_profile(user_id))
```

### Step 6: Pattern Detection
```python
# Analyzer checks query history against rules
history = [
    "marathon shoes",
    "Boston weather",
    "Boston hotels"
]

# Matches "marathon_planning" rule
intent = InferredIntent(
    intent_type="marathon_planning",
    confidence=0.85,
    inferred_categories=["airfare", "travel_packages"]
)
```

### Step 7: Profile Enrichment
```python
# Profile updated with intent
profile.inferred_intents = [intent]
profile.inferred_categories = ["airfare", "travel_packages"]
```

### Step 8: Next Query Benefits
```python
# Next query automatically includes inferred categories
POST /api/retrieve
{
  "query": "running watch",
  "user_id": "user_123"
}

# System adds: ["airfare", "travel_packages"]
# User sees relevant travel ads!
```

## Troubleshooting

### No inferred categories appearing

**Possible causes:**
1. **Not enough queries**: Analysis triggers every 5 queries
   - Solution: Make 5+ queries with same user_id

2. **Pattern not matching**: Confidence below threshold
   - Check logs for pattern detection attempts
   - Adjust `confidence_threshold` in rules
   - Modify pattern keywords to be more flexible

3. **Time window expired**: Queries too far apart
   - Default: 168 hours (7 days)
   - Adjust `time_window_hours` in rules

4. **Profile analysis disabled**: Check configuration
   - Verify `PROFILE_ANALYSIS_ENABLED=true` in `.env`
   - Check server logs for initialization messages

### Profile not persisting

- Profiles are **in-memory only** (no Redis)
- TTL: 7 days (configurable)
- Profiles lost on server restart
- This is intentional for simplicity

### High memory usage

- Default capacity: 10,000 profiles
- Each profile: ~5-10KB
- Total: ~50-100MB
- Adjust `PROFILE_CACHE_SIZE` if needed

## Future Enhancements

1. **Machine Learning**: Replace rule-based detection with ML models
2. **Collaborative Filtering**: Learn from similar users
3. **Real-time Analysis**: Analyze after every query (not just every 5)
4. **Persistent Storage**: Add Redis/PostgreSQL for profile persistence
5. **A/B Testing**: Compare inferred vs. non-inferred performance
6. **Analytics Dashboard**: Visualize pattern detection rates

## Example Scenarios

### Scenario 1: Marathon Planning
```
Query 1: "best marathon running shoes" → Profile created
Query 2: "Boston weather in April" → Location noted
Query 3: "hotels near Boston Marathon" → Pattern detected!
Query 4: "running watch" → Airfare ads now shown
```

### Scenario 2: Vacation Planning
```
Query 1: "vacation destinations" → Profile created
Query 2: "flights to Hawaii" → Location noted
Query 3: "hotels in Maui" → Pattern detected!
Query 4: "beach gear" → Car rental, tours ads shown
```

### Scenario 3: Shopping Research
```
Query 1: "best laptops 2026" → Profile created
Query 2: "laptop prices comparison" → Pattern detected!
Query 3: "gaming mouse" → Coupon, cashback ads shown
```

## API Reference

### Profile-Related Fields

**Request:**
```typescript
interface RetrievalRequest {
  query: string;
  user_id?: string;  // NEW: For profile tracking
  session_id?: string;  // NEW: For session tracking
  context?: UserContext;
}
```

**Response** (unchanged):
```typescript
interface RetrievalResponse {
  ad_eligibility: number;
  extracted_categories: string[];  // Includes inferred categories
  campaigns: Campaign[];
  latency_ms: number;
  metadata: object;
}
```

## Notes

- **Privacy**: User IDs are client-managed, not stored persistently
- **Performance**: Zero latency impact on retrieval
- **Scalability**: In-memory cache limits to ~10k active users
- **Flexibility**: JSON-based rules, no code changes needed
- **Graceful Degradation**: Works without profile system enabled

## Support

For issues or questions:
1. Check server logs for error messages
2. Verify configuration in `.env`
3. Test with `scripts/test_profile_inference.py`
4. Review pattern rules in `data/pattern_rules.json`
