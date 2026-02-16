# iTaK Database Architecture

## At a Glance
- Audience: Operators and developers managing iTaK data stores and memory layers.
- Scope: This page explains `iTaK Database Architecture`.
- Last reviewed: 2026-02-16.

## Quick Start
- Docs hub: [../WIKI.md](../WIKI.md)
- Beginner path: [../NOOBS_FIRST_DAY.md](../NOOBS_FIRST_DAY.md)
- AI-oriented project map: [../AI_CONTEXT.md](../AI_CONTEXT.md)

## Deep Dive
The detailed content for this topic starts below.

## AI Notes
- Preserve database role boundaries (SQLite/Neo4j/Weaviate/SearXNG) when suggesting architecture changes.
- Verify storage and backup procedures against deployed environment constraints before rollout.


Complete guide to all databases used in iTaK.

## Overview

iTaK uses a **4-tier memory architecture** powered by multiple specialized databases:

| Database | Purpose | Auto-Install | Type |
|----------|---------|--------------|------|
| **SQLite** | Fast local storage | ✅ Yes (file-based) | Relational |
| **Neo4j** | Knowledge graph | ✅ Yes (Docker) | Graph |
| **Weaviate** | Vector embeddings | ✅ Yes (Docker) | Vector |
| **SearXNG** | Private web search | ✅ Yes (Docker) | Search Engine |

All databases **auto-install** via `./installers/install-full-stack.sh` in one command!

## 1. SQLite (Layer 1 & 2)

**Purpose:** Fast local storage for recent memories and embeddings

**Location:** `data/db/memory.db`

**Features:**
- No installation required (file-based)
- Auto-created on first run
- Stores recent conversations
- Embedding vectors for quick search
- Persistent across restarts

**Configuration:**
```json
{
  "memory": {
    "sqlite_path": "data/db/memory.db"
  }
}
```

**Access:**
```bash
# View database
sqlite3 data/db/memory.db
sqlite> .tables
sqlite> SELECT * FROM memories LIMIT 10;
```

## 2. Neo4j (Layer 3)

**Purpose:** Knowledge graph for relationships and connected data

**Ports:**
- HTTP: 47474 (Browser UI)
- Bolt: 47687 (Database protocol)

**Features:**
- Entity relationships
- Graph queries (Cypher)
- APOC procedures enabled
- Persistent volumes
- Health checks

**Configuration:**
```bash
# .env file
NEO4J_URI=bolt://localhost:47687
NEO4J_PASSWORD=changeme
```

**Access:**
```bash
# Web Browser
open http://localhost:47474

# Login
Username: neo4j
Password: changeme (or from .env)

# Cypher query example
MATCH (n) RETURN n LIMIT 25;
```

**Auto-Installation:**
```bash
./installers/install-full-stack.sh
# Neo4j auto-installs via Docker
```

**Health Check:**
```bash
curl http://localhost:47474
# Should return Neo4j browser HTML
```

## 3. Weaviate (Layer 4)

**Purpose:** Semantic vector search for long-term memories

**Port:** 48080

**Features:**
- Vector similarity search
- Semantic queries
- Anonymous access enabled
- Persistent storage
- RESTful API

**Configuration:**
```bash
# .env file
WEAVIATE_URL=http://localhost:48080
WEAVIATE_API_KEY=  # Optional (anonymous enabled)
```

**Access:**
```bash
# Check status
curl http://localhost:48080/v1/.well-known/ready

# Query collections
curl http://localhost:48080/v1/schema
```

**Auto-Installation:**
```bash
./installers/install-full-stack.sh
# Weaviate auto-installs via Docker
```

**Health Check:**
```bash
curl http://localhost:48080/v1/.well-known/ready
# Should return {"status":"ok"}
```

## 4. SearXNG (Search Engine)

**Purpose:** Private web search engine (not a database but essential infrastructure)

**Port:** 48888

**Features:**
- Privacy-focused meta-search
- No tracking or logging
- Aggregates results from multiple sources
- Self-hosted
- No API keys required

**Configuration:**
```bash
# .env file
SEARXNG_URL=http://localhost:48888
```

**Access:**
```bash
# Web interface
open http://localhost:48888

# Search API
curl "http://localhost:48888/search?q=artificial+intelligence&format=json"
```

**Auto-Installation:**
```bash
./installers/install-full-stack.sh
# SearXNG auto-installs via Docker
```

**Health Check:**
```bash
curl http://localhost:48888
# Should return HTML page
```

## Installation

### Automatic (Recommended)

**One Command - Installs Everything:**
```bash
./installers/install-full-stack.sh
```

This automatically:
1. ✅ Installs Docker (if missing)
2. ✅ Creates .env configuration
3. ✅ Pulls all database images
4. ✅ Starts all services
5. ✅ Waits for health checks
6. ✅ Shows connection info

**Time:** ~5 minutes on first run

### Manual Installation

If you prefer manual setup:

```bash
# 1. Create .env
cp install/config/.env.example .env

# 2. Edit .env with passwords
nano .env

# 3. Start services
docker compose --project-directory . -f install/docker/docker-compose.yml up -d

# 4. Wait for services to be ready
./install/check-databases.sh
```

## Verification

### Check All Databases

```bash
./install/check-databases.sh
```

**Output:**
```
🔍 iTaK Database Status Checker
════════════════════════════════════════

Neo4j (Knowledge Graph):     ✅ Running (http://localhost:47474)
Weaviate (Vector Database):  ✅ Running (http://localhost:48080)
SearXNG (Search Engine):     ✅ Running (http://localhost:48888)
SQLite (Local Storage):      ✅ Initialized (data/db/memory.db)

════════════════════════════════════════
🎉 All databases are running!
```

### Check Docker Containers

```bash
docker ps | grep itak
```

**Should show:**
```
itak-neo4j      (healthy)
itak-weaviate   (healthy)
itak-searxng    (healthy)
```

### Check Health Status

```bash
docker compose --project-directory . -f install/docker/docker-compose.yml ps
```

**Healthy services show:**
- `State: Up (healthy)`
- `Status: Up X seconds (healthy)`

## Data Persistence

All databases use Docker volumes for persistent storage:

```bash
# List volumes
docker volume ls | grep itak

# Should show:
itak_neo4j-data
itak_neo4j-logs
itak_weaviate-data
itak_searxng-data
```

**Data survives:**
- ✅ Container restarts
- ✅ System reboots
- ✅ Docker updates
- ✅ iTaK updates

**Data is lost when:**
- ❌ `docker compose --project-directory . -f install/docker/docker-compose.yml down -v` (volumes deleted)
- ❌ Manual volume deletion

## Backup & Restore

### Backup All Data

```bash
# Stop services first
docker compose --project-directory . -f install/docker/docker-compose.yml down

# Backup volumes
docker run --rm \
  -v itak_neo4j-data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/neo4j-backup.tar.gz /data

docker run --rm \
  -v itak_weaviate-data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/weaviate-backup.tar.gz /data

# Backup SQLite
cp data/db/memory.db backups/memory-backup.db

# Restart services
docker compose --project-directory . -f install/docker/docker-compose.yml up -d
```

### Restore from Backup

```bash
# Stop services
docker compose --project-directory . -f install/docker/docker-compose.yml down

# Restore Neo4j
docker run --rm \
  -v itak_neo4j-data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar xzf /backup/neo4j-backup.tar.gz -C /

# Restore Weaviate
docker run --rm \
  -v itak_weaviate-data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar xzf /backup/weaviate-backup.tar.gz -C /

# Restore SQLite
cp backups/memory-backup.db data/db/memory.db

# Restart services
docker compose --project-directory . -f install/docker/docker-compose.yml up -d
```

## Troubleshooting

### Database Not Starting

**Check logs:**
```bash
docker compose --project-directory . -f install/docker/docker-compose.yml logs neo4j
docker compose --project-directory . -f install/docker/docker-compose.yml logs weaviate
docker compose --project-directory . -f install/docker/docker-compose.yml logs searxng
```

**Common issues:**
- Port already in use → Change port in .env
- Insufficient memory → Increase Docker memory limit
- Permission denied → Check volume permissions

### Database Not Responding

**Restart specific service:**
```bash
docker compose --project-directory . -f install/docker/docker-compose.yml restart neo4j
docker compose --project-directory . -f install/docker/docker-compose.yml restart weaviate
docker compose --project-directory . -f install/docker/docker-compose.yml restart searxng
```

**Restart all:**
```bash
docker compose --project-directory . -f install/docker/docker-compose.yml restart
```

### Reset Database

**⚠️ WARNING: This deletes all data**

```bash
# Stop services
docker compose --project-directory . -f install/docker/docker-compose.yml down

# Delete volumes
docker volume rm itak_neo4j-data itak_neo4j-logs
docker volume rm itak_weaviate-data
docker volume rm itak_searxng-data
rm -f data/db/memory.db

# Restart (creates fresh databases)
docker compose --project-directory . -f install/docker/docker-compose.yml up -d
```

### Port Conflicts

If ports are already in use, change them in `.env`:

```bash
# .env
NEO4J_HTTP_PORT=47474  # Change to 7474, 17474, etc.
NEO4J_BOLT_PORT=47687  # Change to 7687, 17687, etc.
WEAVIATE_PORT=48080    # Change to 8080, 18080, etc.
SEARXNG_PORT=48888     # Change to 8888, 18888, etc.
```

Then restart:
```bash
docker compose --project-directory . -f install/docker/docker-compose.yml down
docker compose --project-directory . -f install/docker/docker-compose.yml up -d
```

## Performance Tuning

### Neo4j

**Increase memory:**
```yaml
# install/docker/docker-compose.yml
environment:
  NEO4J_server_memory_heap_initial__size: "512m"  # Default: 256m
  NEO4J_server_memory_heap_max__size: "1g"        # Default: 512m
```

### Weaviate

**Adjust for large datasets:**
```yaml
# install/docker/docker-compose.yml
environment:
  QUERY_DEFAULTS_LIMIT: 100  # Default: 25
```

### Docker Resources

**Increase Docker limits:**
```bash
# Docker Desktop → Settings → Resources
# Recommended for full stack:
# - CPUs: 4+
# - Memory: 8GB+
# - Disk: 20GB+
```

## Resource Usage

| Database | Disk Space | RAM Usage | CPU Usage |
|----------|------------|-----------|-----------|
| SQLite | ~10-100MB | Minimal | Minimal |
| Neo4j | ~500MB-2GB | 256-512MB | Low-Medium |
| Weaviate | ~1-5GB | 512MB-1GB | Low-Medium |
| SearXNG | ~100-500MB | 128-256MB | Low |
| **Total** | **~2-8GB** | **~1-2GB** | **Low-Medium** |

## Security

### Default Passwords

**Change these in production:**

```bash
# .env
NEO4J_PASSWORD=changeme          # ⚠️ Change this!
WEBUI_PASSWORD=changeme          # ⚠️ Change this!
```

### Network Access

By default, databases are only accessible from localhost:

- ✅ localhost:47474 → Accessible
- ❌ 0.0.0.0:47474 → Not accessible

To allow external access (not recommended):
```yaml
# install/docker/docker-compose.yml
ports:
  - "0.0.0.0:47474:7474"  # Allow all IPs
```

### Firewall

If running on a server, block database ports:

```bash
# UFW (Ubuntu)
sudo ufw deny 47474
sudo ufw deny 47687
sudo ufw deny 48080
sudo ufw deny 48888

# Only allow iTaK web UI
sudo ufw allow 8000
```

## Summary

**All databases auto-install with one command:**
```bash
./installers/install-full-stack.sh
```

**Verify everything is running:**
```bash
./install/check-databases.sh
```

**That's it!** 🎉

All databases are configured, running, and ready to use.
