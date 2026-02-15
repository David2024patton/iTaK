# iTaK - MEMORY.md
# Key Decisions, Lessons Learned, Important Facts
# This file grows as the agent accumulates knowledge.

## Architecture Decisions

- **4-model architecture** adopted from Agent Zero - separates costly reasoning from cheap utility tasks
- **Extension hooks over plugin system** - simpler, more hackable, convention-based
- **SQLite for fast retrieval** - Neo4j and Weaviate are upgrades on top, not replacements
- **Markdown files as source of truth** - human-readable, version-controllable, any agent can understand

## Setup & Installation

- **Interactive setup script** - Run `python installers/setup.py` for guided configuration of Neo4j and Weaviate
- **Neo4j is optional** - iTaK works with SQLite-only memory; Neo4j adds knowledge graph layer
- **Docker-based installation** - Setup script can install Neo4j via Docker Compose if user doesn't have their own instance
- **Manual configuration supported** - Users can skip setup script and manually edit .env and config.json

## Lessons Learned

<!-- Agent will append lessons here as it learns -->

## Important Facts

<!-- Agent will append facts here as it discovers them -->

## MemU Extraction - 2026-02-13 22:37
- Fact one
- Fact two

## MemU Extraction - 2026-02-13 22:37
- Complex fact

## MemU Extraction - 2026-02-13 22:38
- Fact one
- Fact two

## MemU Extraction - 2026-02-13 22:38
- Complex fact

## MemU Extraction - 2026-02-13 22:38
- Fact one
- Fact two

## MemU Extraction - 2026-02-13 22:38
- Complex fact

## MemU Extraction - 2026-02-13 22:40
- Fact one
- Fact two

## MemU Extraction - 2026-02-13 22:40
- Complex fact
