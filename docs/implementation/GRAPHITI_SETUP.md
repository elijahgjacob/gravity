# Graphiti + Neo4j Setup Guide

This guide will help you set up and run Graphiti with Neo4j for the Ad Retrieval System.

## Quick Start (Recommended)

### Option 1: Using Docker Compose (Easiest)

```bash
# 1. Start Neo4j
./scripts/start_graphiti.sh

# 2. Verify it's working
python scripts/test_graphiti.py

# 3. Start your API
uvicorn src.api.main:app --reload
```

### Option 2: Using Setup Script

```bash
# 1. Run the setup script
./scripts/setup_neo4j.sh

# 2. Verify it's working
python scripts/test_graphiti.py

# 3. Start your API
uvicorn src.api.main:app --reload
```

## Prerequisites

1. **Docker Desktop** (required)
   - Download: https://www.docker.com/products/docker-desktop
   - Make sure Docker is running before proceeding

2. **OpenRouter API Key** (required for Graphiti)
   - Sign up: https://openrouter.ai/
   - Get your API key from the dashboard
   - Add credits to your account ($5 minimum recommended)

## Step-by-Step Setup

### Step 1: Configure Environment

Update your `.env` file:

```env
# Enable Graphiti
GRAPHITI_ENABLED=true

# Neo4j Configuration
GRAPHITI_NEO4J_URI=bolt://localhost:7687
GRAPHITI_NEO4J_USER=neo4j
GRAPHITI_NEO4J_PASSWORD=password

# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# LLM Model (choose one)
GRAPHITI_LLM_MODEL=anthropic/claude-3.5-sonnet  # Recommended
# GRAPHITI_LLM_MODEL=openai/gpt-3.5-turbo      # Cheaper
# GRAPHITI_LLM_MODEL=openai/gpt-4              # Best quality

# Namespace
GRAPHITI_NAMESPACE=ad_retrieval
```

### Step 2: Start Neo4j

**Using Docker Compose (recommended):**

```bash
# Start Neo4j
docker compose up -d neo4j

# Check status
docker compose ps

# View logs
docker compose logs neo4j

# Stop Neo4j
docker compose down
```

**Using the setup script:**

```bash
./scripts/setup_neo4j.sh
```

**Manual Docker command:**

```bash
docker run -d \
  --name gravity-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc"]' \
  -v $(pwd)/neo4j_data:/data \
  neo4j:5.26
```

### Step 3: Verify Neo4j is Running

**Check container status:**
```bash
docker ps | grep neo4j
```

**Access Neo4j Browser:**
- Open: http://localhost:7474
- Username: `neo4j`
- Password: `password`

**Test connection:**
```bash
curl http://localhost:7474
```

### Step 4: Test Graphiti Integration

```bash
python scripts/test_graphiti.py
```

Expected output:
```
==============================================================
Testing Graphiti + Neo4j Connection
==============================================================

Configuration:
  GRAPHITI_ENABLED: True
  NEO4J_URI: bolt://localhost:7687
  ...

✓ Dependencies initialized

Dependency Status:
  ✓ graphiti: True
  ✓ blocklist: True
  ...

==============================================================
✅ SUCCESS! Graphiti + Neo4j are working!
==============================================================
```

### Step 5: Start Your API

```bash
uvicorn src.api.main:app --reload
```

Look for this in the logs:
```
✓ Graphiti repository initialized (using OpenRouter)
```

### Step 6: Make a Test Request

```bash
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "running shoes for marathon",
    "context": {"age": 30, "gender": "male"}
  }'
```

### Step 7: View Data in Neo4j

1. Open Neo4j Browser: http://localhost:7474
2. Run a query to see recorded data:

```cypher
// See all nodes
MATCH (n) RETURN n LIMIT 25

// See recent episodes
MATCH (e:Episode)
RETURN e.name, e.created_at
ORDER BY e.created_at DESC
LIMIT 10

// See relationships
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 25
```

## Common Commands

### Docker Compose Commands

```bash
# Start Neo4j
docker compose up -d neo4j

# Stop Neo4j
docker compose down

# Restart Neo4j
docker compose restart neo4j

# View logs
docker compose logs neo4j -f

# Check status
docker compose ps
```

### Docker Commands (if not using compose)

```bash
# Start
docker start gravity-neo4j

# Stop
docker stop gravity-neo4j

# Restart
docker restart gravity-neo4j

# View logs
docker logs gravity-neo4j -f

# Remove (deletes container, not data)
docker rm gravity-neo4j

# Remove with data
docker rm gravity-neo4j
rm -rf neo4j_data neo4j_logs
```

### Python Test Commands

```bash
# Test Graphiti connection
python scripts/test_graphiti.py

# Run unit tests
pytest tests/unit/test_graphiti_*.py -v

# Run integration tests
pytest tests/integration/test_graphiti/ -v

# Run all Graphiti tests
pytest -k graphiti -v
```

## Troubleshooting

### Issue: "Docker is not running"

**Solution:**
1. Open Docker Desktop
2. Wait for it to start (green icon in menu bar)
3. Try again

### Issue: "Port 7474 or 7687 already in use"

**Solution:**
```bash
# Find what's using the port
lsof -ti:7474
lsof -ti:7687

# Stop existing Neo4j
docker stop gravity-neo4j
docker rm gravity-neo4j

# Or kill the process
lsof -ti:7474 | xargs kill
```

### Issue: "Graphiti initialization failed: OpenAIClient.__init__() got an unexpected keyword argument 'api_key'"

**Solution:**
This is a known issue with the current version of graphiti-core. The system will gracefully degrade and work without Graphiti. To fix:

1. Check if there's a newer version of graphiti-core:
   ```bash
   pip install --upgrade graphiti-core
   ```

2. Or wait for the fix and use the system without Graphiti (it works perfectly!)

### Issue: "Connection refused to Neo4j"

**Solution:**
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check Neo4j logs
docker logs gravity-neo4j

# Restart Neo4j
docker restart gravity-neo4j

# Wait 30 seconds for Neo4j to start
sleep 30
python scripts/test_graphiti.py
```

### Issue: "OpenRouter API key invalid"

**Solution:**
1. Verify your API key at: https://openrouter.ai/
2. Check you have credits in your account
3. Update `.env` with the correct key
4. Restart your API server

### Issue: "Neo4j Browser shows 'ServiceUnavailable'"

**Solution:**
```bash
# Check Neo4j is healthy
docker compose ps

# Check logs for errors
docker compose logs neo4j

# Restart Neo4j
docker compose restart neo4j

# Wait for startup
sleep 30
```

## Performance Tuning

### Adjust Neo4j Memory

Edit `docker-compose.yml`:

```yaml
environment:
  - NEO4J_server_memory_heap_initial__size=1G
  - NEO4J_server_memory_heap_max__size=2G
```

### Choose Faster LLM Model

In `.env`:

```env
# Fastest and cheapest
GRAPHITI_LLM_MODEL=openai/gpt-3.5-turbo

# Balanced (recommended)
GRAPHITI_LLM_MODEL=anthropic/claude-3.5-sonnet

# Best quality
GRAPHITI_LLM_MODEL=openai/gpt-4
```

## Cost Estimation

### OpenRouter Costs (per 1000 queries)

| Model | Cost per Query | Monthly (1K queries/day) |
|-------|---------------|--------------------------|
| gpt-3.5-turbo | $0.0001 | ~$3 |
| gemini-pro | $0.0002 | ~$6 |
| claude-3.5-sonnet | $0.0005 | ~$15 |
| gpt-4 | $0.001 | ~$30 |

### Neo4j Costs

- **Docker (Local)**: Free
- **Neo4j Aura Free**: Free (up to 50K nodes)
- **Neo4j Aura Pro**: $65/month (starts at)

## Data Management

### Backup Neo4j Data

```bash
# Stop Neo4j
docker compose down

# Backup data directory
tar -czf neo4j_backup_$(date +%Y%m%d).tar.gz neo4j_data/

# Restart Neo4j
docker compose up -d neo4j
```

### Clear All Data

```bash
# Stop Neo4j
docker compose down

# Remove data
rm -rf neo4j_data neo4j_logs

# Restart Neo4j (will create fresh database)
docker compose up -d neo4j
```

### Query Data Retention

Delete old episodes (run in Neo4j Browser):

```cypher
// Delete episodes older than 90 days
MATCH (e:Episode)
WHERE e.created_at < datetime() - duration('P90D')
DELETE e
```

## Production Deployment

### Use Neo4j Aura (Cloud)

1. Sign up: https://neo4j.com/cloud/aura/
2. Create a database
3. Update `.env`:

```env
GRAPHITI_NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
GRAPHITI_NEO4J_USER=neo4j
GRAPHITI_NEO4J_PASSWORD=your-generated-password
```

### Secure Your Setup

1. **Change default password:**
   ```env
   GRAPHITI_NEO4J_PASSWORD=your-secure-password-here
   ```

2. **Restrict network access:**
   - Use firewall rules
   - Only allow connections from your API server

3. **Use environment variables:**
   - Never commit `.env` to git
   - Use secrets management in production

## Next Steps

Once Graphiti is running:

1. **Monitor your knowledge graph:**
   - Open Neo4j Browser
   - Run queries to see patterns
   - Track user journeys

2. **Build analytics:**
   - Query campaign co-occurrences
   - Analyze user behavior patterns
   - Identify trending categories

3. **Enhance ranking:**
   - Use graph data for personalization
   - Implement collaborative filtering
   - Pre-compute campaign relationships

## Support

- **Graphiti Documentation**: https://help.getzep.com/graphiti
- **Neo4j Documentation**: https://neo4j.com/docs/
- **OpenRouter**: https://openrouter.ai/docs

## Quick Reference

```bash
# Start everything
docker compose up -d && python scripts/test_graphiti.py

# Stop everything
docker compose down

# View logs
docker compose logs -f

# Restart API with Graphiti
uvicorn src.api.main:app --reload

# Test end-to-end
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "context": null}'
```
