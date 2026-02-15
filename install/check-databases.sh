#!/bin/bash
# iTaK Database Status Checker
# Verifies all databases are running and accessible

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 iTaK Database Status Checker"
echo "════════════════════════════════════════"
echo ""

# Check if Docker is running
if ! docker ps >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker first"
    exit 1
fi

# Check each database
check_neo4j() {
    echo -n "Neo4j (Knowledge Graph):     "
    if docker ps | grep -q "itak-neo4j"; then
        if curl -s http://localhost:47474 >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Running${NC} (http://localhost:47474)"
            return 0
        else
            echo -e "${YELLOW}⚠️  Container running but not responding${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Not running${NC}"
        return 1
    fi
}

check_weaviate() {
    echo -n "Weaviate (Vector Database):  "
    if docker ps | grep -q "itak-weaviate"; then
        if curl -s http://localhost:48080/v1/.well-known/ready >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Running${NC} (http://localhost:48080)"
            return 0
        else
            echo -e "${YELLOW}⚠️  Container running but not responding${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Not running${NC}"
        return 1
    fi
}

check_searxng() {
    echo -n "SearXNG (Search Engine):     "
    if docker ps | grep -q "itak-searxng"; then
        if curl -s http://localhost:48888 >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Running${NC} (http://localhost:48888)"
            return 0
        else
            echo -e "${YELLOW}⚠️  Container running but not responding${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Not running${NC}"
        return 1
    fi
}

check_sqlite() {
    echo -n "SQLite (Local Storage):      "
    if [ -f "data/db/memory.db" ]; then
        echo -e "${GREEN}✅ Initialized${NC} (data/db/memory.db)"
        return 0
    else
        echo -e "${YELLOW}⚠️  Will be created on first run${NC}"
        return 0
    fi
}

# Run checks
ERRORS=0
check_neo4j || ((ERRORS++))
check_weaviate || ((ERRORS++))
check_searxng || ((ERRORS++))
check_sqlite

echo ""
echo "════════════════════════════════════════"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 All databases are running!${NC}"
    echo ""
    echo "Connection Details:"
    echo ""
    echo "  Neo4j:    bolt://localhost:47687"
    echo "            Username: neo4j"
    echo "            Password: changeme (or from .env)"
    echo ""
    echo "  Weaviate: http://localhost:48080"
    echo ""
    echo "  SearXNG:  http://localhost:48888"
    echo ""
    echo "  SQLite:   data/db/memory.db"
    echo ""
elif [ $ERRORS -eq 3 ]; then
    echo -e "${RED}❌ No databases are running${NC}"
    echo ""
    echo "To start all databases:"
    echo "  ./installers/install-full-stack.sh"
    echo ""
    echo "Or manually:"
    echo "  docker compose --project-directory . -f install/docker/docker-compose.yml up -d"
    echo ""
else
    echo -e "${YELLOW}⚠️  Some databases are not running ($ERRORS issues)${NC}"
    echo ""
    echo "To start all databases:"
    echo "  docker compose --project-directory . -f install/docker/docker-compose.yml up -d"
    echo ""
    echo "To check container status:"
    echo "  docker ps -a | grep itak"
    echo ""
    echo "To view logs:"
    echo "  docker compose --project-directory . -f install/docker/docker-compose.yml logs"
    echo ""
fi

echo "════════════════════════════════════════"
exit $ERRORS
