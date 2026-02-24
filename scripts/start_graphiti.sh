#!/bin/bash
# Quick start script for Graphiti with Neo4j

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=================================================="
echo "Starting Graphiti + Neo4j"
echo "=================================================="
echo ""

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}Error: docker-compose not found${NC}"
    echo "Please install docker-compose or use Docker Desktop"
    exit 1
fi

# Start Neo4j using docker-compose
cd "$(dirname "$0")/.."

echo "Starting Neo4j container..."
$COMPOSE_CMD up -d neo4j

echo ""
echo "Waiting for Neo4j to be ready..."
sleep 5

# Check if Neo4j is healthy
RETRY_COUNT=0
MAX_RETRIES=30

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if $COMPOSE_CMD ps neo4j | grep -q "healthy"; then
        echo -e "${GREEN}✓ Neo4j is healthy and ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}Warning: Neo4j health check timed out${NC}"
    echo "Neo4j may still be starting. Check with: $COMPOSE_CMD logs neo4j"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}Graphiti + Neo4j Started!${NC}"
echo "=================================================="
echo ""
echo "Connection Details:"
echo "  Browser UI: http://localhost:7474"
echo "  Bolt URI: bolt://localhost:7687"
echo "  Username: neo4j"
echo "  Password: password"
echo ""
echo "Verify with:"
echo "  $COMPOSE_CMD ps"
echo "  $COMPOSE_CMD logs neo4j"
echo ""
echo "Stop with:"
echo "  $COMPOSE_CMD down"
echo ""
