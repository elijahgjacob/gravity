# Ad Retrieval System

## Overview

Build the first half of an ad retrieval pipeline that processes user queries with context, determines commercial intent, and retrieves relevant advertising campaigns—all within a **100ms latency budget**.

You will implement a system that:
1. Accepts a user query with optional user context
2. Classifies whether the query has commercial intent (binary)
3. Extracts relevant product/service categories
4. Searches and ranks campaigns by relevancy, returning the top 1,000 candidates

## Provided Resources

- **OpenRouter API Key**: Access to LLMs via OpenRouter (provided separately)
- **Railway Compute**: On-demand instances for hosting services if needed
- **Starter schema**: See [Input/Output Specification](#inputoutput-specification) below

You are free to use any additional tools, libraries, or services you see fit.

---

## Requirements

### 1. API Endpoint

Implement a single HTTP endpoint that accepts a POST request:

```
POST /api/retrieve
```

**Latency Target**: End-to-end response must complete in **< 100ms** (p95)

### 2. Input/Output Specification

**Request Body:**
```json
{
  "query": "I'm running a marathon next month and need new shoes. What should I get?",
  "context": {
    "gender": "male",
    "age": 24,
    "location": "San Francisco, CA",
    "interests": ["fitness", "outdoor activities"]
  }
}
```

- `query` (string, required): The user's natural language query
- `context` (object, optional): Arbitrary user context (demographics, interests, device info, etc.)

**Response Body:**
```json
{
  "ad_eligibility": 0.85,
  "extracted_categories": ["running shoes", "marathon training gear", "athletic footwear"],
  "campaigns": [
    {
      "campaign_id": "camp_123",
      "relevance_score": 0.94,
      "...": "additional fields you choose to include"
    }
  ],
  "latency_ms": 87,
  "metadata": {}
}
```

- `ad_eligibility` (number, 0.0-1.0): How appropriate it is to show ads for this query
- `extracted_categories` (array of strings): Product/service categories relevant to the query
- `campaigns` (array): Top 1,000 campaigns ordered by relevance (descending)
- `latency_ms` (number): Actual processing time
- `metadata` (object): Any debugging info, model names, intermediate scores, etc.

### 3. Synthetic Campaign Data

Create a synthetic dataset of campaigns for your system to search. Your dataset should:

- Contain **at least 10,000 campaigns** across diverse verticals
- Include fields necessary for relevance matching (you decide the schema)
- Be realistic enough to demonstrate meaningful ranking

Document your data generation approach and any assumptions made.

### 4. Ad Eligibility Scoring

Implement a scoring function that determines whether it's **appropriate** to show an ad for a given query. This is not about purchase intent—many informational queries can surface relevant ads. Instead, this filters queries where advertising would be inappropriate, insensitive, or unwelcome.

**Return a score from 0.0 to 1.0** where:
- `1.0` = Perfectly appropriate to show ads
- `0.0` = Do not show ads under any circumstances

**High eligibility (0.8 - 1.0):**
- "Best running shoes for flat feet" → `0.95`
- "What is the history of the marathon?" → `0.85` (could show marathon gear)
- "Why do runners get blisters?" → `0.80` (could show blister prevention products)

**Medium eligibility (0.4 - 0.7):**
- "I'm feeling really stressed about work" → `0.5` (contextual, could go either way)
- "How do I file for unemployment?" → `0.4` (sensitive financial situation)

**Low eligibility - DO NOT SHOW ADS (0.0 - 0.3):**
- "My mom just passed away" → `0.0`
- "I'm having thoughts of self-harm" → `0.0`
- "How to make a pipe bomb" → `0.0`
- Explicit NSFW content → `0.0`
- Hate speech or violent content → `0.0`

Your scoring should handle edge cases gracefully. When in doubt, err on the side of caution—a missed ad opportunity is better than an insensitive one.

### 5. Category Extraction

Extract product/service categories that would be relevant for ad matching.

For the query *"I'm running a marathon next month and need new shoes"*, good extractions might include:
- Running shoes
- Marathon training gear
- Athletic socks
- Sports nutrition
- Fitness tracking devices

Categories should be specific enough to enable precise matching but general enough to surface a reasonable number of campaigns.

### 6. Campaign Retrieval & Ranking

Search your campaign dataset and return the **top 1,000 most relevant campaigns** ordered by relevance score.

Your ranking should consider:
- Semantic similarity between query/categories and campaign content
- User context when relevant (e.g., location-based campaigns, demographic targeting)
- Any other signals you believe improve relevance

---

## Evaluation Criteria

### Architecture & Design (25%)

| Criteria | What We're Looking For |
|----------|----------------------|
| System design | Clear separation of concerns, appropriate component boundaries |
| Latency optimization | Thoughtful approach to meeting the 100ms budget (parallelization, caching, model selection, etc.) |
| Scalability considerations | How would this handle 10x the campaign corpus? 100x QPS? |
| Trade-off articulation | Document the trade-offs you made and why |

### Ad Eligibility Scoring (20%)

| Criteria | What We're Looking For |
|----------|----------------------|
| Safety filtering | Correctly identifies queries where ads should NOT be shown (NSFW, tragedy, harm) |
| Score calibration | Scores are meaningful and consistent (0.9 vs 0.5 reflects real difference) |
| Efficiency | Scoring doesn't dominate the latency budget |
| Edge case handling | Reasonable behavior on ambiguous or borderline queries |

### Category Extraction (20%)

| Criteria | What We're Looking For |
|----------|----------------------|
| Relevance | Extracted categories would actually match useful campaigns |
| Granularity | Neither too broad nor too narrow |
| Context utilization | User context influences extraction when appropriate |
| Robustness | Handles varied query formats (questions, statements, fragments) |

### Retrieval & Ranking (25%)

| Criteria | What We're Looking For |
|----------|----------------------|
| Ranking quality | Top results are meaningfully more relevant than lower results |
| Search implementation | Efficient retrieval from 10k+ campaigns |
| Embedding/indexing strategy | Appropriate choice for the latency and quality requirements |
| Score calibration | Relevance scores are interpretable and consistent |

### Code Quality & Documentation (10%)

| Criteria | What We're Looking For |
|----------|----------------------|
| Code organization | Readable, maintainable, appropriately commented |
| Documentation | Clear README, setup instructions, API documentation |
| Testing | Evidence of testing (unit tests, integration tests, or manual test cases) |
| Error handling | Graceful degradation, meaningful error messages |

---

## Deliverables

1. **Source code** in a Git repository (GitHub, GitLab, etc.)
2. **README.md** with:
   - Setup and run instructions
   - Architecture overview
   - Key design decisions and trade-offs
   - Latency breakdown (where time is spent)
3. **Test queries** demonstrating the system's behavior (at least 10 diverse examples)
4. **Synthetic data generation script** or documentation of how data was created

---

## Constraints & Guidelines

### Must Have
- Response latency < 100ms (p95)
- At least 10,000 searchable campaigns
- Return exactly 1,000 campaigns per request (or all if fewer exist)
- Ad eligibility score (0.0 - 1.0)
- Category extraction (1-10 categories per query)

### May Use
- Any programming language (Python recommended for ML ecosystem)
- Any vector database (Qdrant, Pinecone, Weaviate, pgvector, FAISS, etc.)
- Any LLM via OpenRouter (be mindful of latency)
- Any embedding model (consider hosted vs. local trade-offs)
- Caching layers (Redis, in-memory, etc.)
- Pre-computation / indexing

### Should Avoid
- Hardcoded responses or excessive special-casing
- Ignoring the latency requirement (100ms is a hard constraint)
- Over-engineering (this is a 72-hour project)

---

## Guidance on Approach

This is an open-ended problem with many valid solutions. Here are some dimensions to consider:

**LLM Usage**: LLMs are powerful but slow. Consider where an LLM adds value vs. where simpler methods suffice. Structured output, prompt engineering, and model selection all matter.

**Embedding Strategy**: Pre-computed campaign embeddings enable fast similarity search. Consider what text to embed and how to combine query + context.

**Hybrid Approaches**: Combining fast heuristics with semantic understanding often outperforms either alone.

**Latency Budgeting**: If you have 100ms total, how do you allocate it? Intent classification, embedding, search, and ranking must all fit.

---

## Questions?

If you have clarifying questions during the project, document your assumptions and proceed. We're evaluating your decision-making as much as your implementation.

---

## Submission

Reply to the email with:
1. Link to your repository
2. Brief summary of your approach (2-3 paragraphs)
3. One thing you would improve with more time

**Deadline**: 72 hours from receipt of this document
