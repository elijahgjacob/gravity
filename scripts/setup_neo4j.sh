#!/bin/bash
# Setup script for Neo4j with Docker

set -e

echo "=================================================="
echo "Neo4j Setup for Graphiti Integration"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
NEO4J_CONTAINER_NAME="gravity-neo4j"
NEO4J_VERSION="5.26"
NEO4J_HTTP_PORT="7474"
NEO4J_BOLT_PORT="7687"
NEO4J_PASSWORD="password"  # Change this in production!

echo "Configuration:"
echo "  Container Name: $NEO4J_CONTAINER_NAME"
echo "  Neo4j Version: $NEO4J_VERSION"
echo "  HTTP Port: $NEO4J_HTTP_PORT (Browser UI)"
echo "  Bolt Port: $NEO4J_BOLT_PORT (Database)"
echo "  Password: $NEO4J_PASSWORD"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed and running${NC}"
echo ""

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${NEO4J_CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Container '$NEO4J_CONTAINER_NAME' already exists${NC}"
    echo ""
    echo "Options:"
    echo "  1) Remove and recreate"
    echo "  2) Start existing container"
    echo "  3) Cancel"
    echo ""
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            echo "Stopping and removing existing container..."
            docker stop $NEO4J_CONTAINER_NAME 2>/dev/null || true
            docker rm $NEO4J_CONTAINER_NAME 2>/dev/null || true
            echo -e "${GREEN}✓ Existing container removed${NC}"
            ;;
        2)
            echo "Starting existing container..."
            docker start $NEO4J_CONTAINER_NAME
            echo -e "${GREEN}✓ Container started${NC}"
            echo ""
            echo "Neo4j is now running!"
            echo "  Browser UI: http://localhost:$NEO4J_HTTP_PORT"
            echo "  Bolt URI: bolt://localhost:$NEO4J_BOLT_PORT"
            echo "  Username: neo4j"
            echo "  Password: $NEO4J_PASSWORD"
            exit 0
            ;;
        3)
            echo "Cancelled"
            exit 0
            ;;
        *)
            echo "Invalid option"
            exit 1
            ;;
    esac
fi

echo "Creating Neo4j container..."
echo ""

# Create data directory for persistence
DATA_DIR="$(pwd)/neo4j_data"
mkdir -p "$DATA_DIR"

# Run Neo4j container
docker run -d \
  --name $NEO4J_CONTAINER_NAME \
  -p $NEO4J_HTTP_PORT:7474 \
  -p $NEO4J_BOLT_PORT:7687 \
  -e NEO4J_AUTH=neo4j/$NEO4J_PASSWORD \
  -e NEO4J_PLUGINS='["apoc"]' \
  -e NEO4J_server_memory_heap_initial__size=512m \
  -e NEO4J_server_memory_heap_max__size=1G \
  -v "$DATA_DIR:/data" \
  neo4j:$NEO4J_VERSION

echo -e "${GREEN}✓ Neo4j container created${NC}"
echo ""

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to start (this may take 30-60 seconds)..."
RETRY_COUNT=0
MAX_RETRIES=30

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker logs $NEO4J_CONTAINER_NAME 2>&1 | grep -q "Started."; then
        echo -e "${GREEN}✓ Neo4j is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}Warning: Neo4j may still be starting${NC}"
    echo "Check status with: docker logs $NEO4J_CONTAINER_NAME"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}Neo4j Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Connection Details:"
echo "  Browser UI: http://localhost:$NEO4J_HTTP_PORT"
echo "  Bolt URI: bolt://localhost:$NEO4J_BOLT_PORT"
echo "  Username: neo4j"
echo "  Password: $NEO4J_PASSWORD"
echo ""
echo "Useful Commands:"
echo "  Stop:    docker stop $NEO4J_CONTAINER_NAME"
echo "  Start:   docker start $NEO4J_CONTAINER_NAME"
echo "  Restart: docker restart $NEO4J_CONTAINER_NAME"
echo "  Logs:    docker logs $NEO4J_CONTAINER_NAME"
echo "  Remove:  docker stop $NEO4J_CONTAINER_NAME && docker rm $NEO4J_CONTAINER_NAME"
echo ""
echo "Next Steps:"
echo "  1. Update .env with: GRAPHITI_ENABLED=true"
echo "  2. Restart your API server"
echo "  3. Check logs for: '✓ Graphiti repository initialized'"
echo ""
