"""
iTaK Neo4j Knowledge Graph - Layer 3 of the 4-layer brain.
Stores entities, relationships, and contextual knowledge.
"""

import logging

try:
    from neo4j import GraphDatabase  # Backward-compatible patch target for tests
except Exception:
    GraphDatabase = None

logger = logging.getLogger(__name__)


class Neo4jStore:
    """Neo4j-backed knowledge graph for relationship-aware memory.

    Layer 3 of the 4-layer brain:
    - Layer 1: Markdown files (source of truth)
    - Layer 2: SQLite + embeddings (fast retrieval)
    - Layer 3: Neo4j (relationships) ← THIS
    - Layer 4: Weaviate (semantic search)

    Stores:
    - Entities (people, projects, tools, concepts)
    - Relationships (uses, depends_on, related_to, etc.)
    - Temporal context (when things happened)
    """

    def __init__(self, config: dict):
        self.config = config
        self.uri = config.get("uri", "bolt://localhost:7687")
        self.user = config.get("user", "neo4j")
        self.password = config.get("password", "")
        self.driver = None
        self._connected = False

    async def connect(self):
        """Connect to Neo4j."""
        try:
            from neo4j import AsyncGraphDatabase

            self.driver = AsyncGraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            # Verify connectivity
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            self._connected = True
            logger.info(f"Connected to Neo4j at {self.uri}")

            # Create indexes
            await self._create_indexes()
        except ImportError:
            logger.warning("neo4j driver not installed. Run: pip install neo4j")
            self._connected = False
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}")
            self._connected = False

    async def _create_indexes(self):
        """Create necessary indexes and constraints."""
        if not self._connected:
            return

        queries = [
            "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX IF NOT EXISTS FOR (m:Memory) ON (m.category)",
            "CREATE INDEX IF NOT EXISTS FOR (m:Memory) ON (m.created_at)",
            "CREATE INDEX IF NOT EXISTS FOR (t:Tool) ON (t.name)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Skill) ON (s.name)",
        ]
        async with self.driver.session() as session:
            for q in queries:
                try:
                    await session.run(q)
                except Exception:
                    pass

    async def save_entity(
        self,
        name: str | None = None,
        entity_type: str = "Entity",
        properties: dict | None = None,
        entity_id: str | None = None,
    ) -> str:
        """Save or update an entity node."""
        if name is None:
            name = entity_id or ""
        if not self._connected:
            return name

        props = properties or {}
        props["name"] = name
        props["type"] = entity_type

        query = """
        MERGE (e:Entity {name: $name, type: $type})
        SET e += $props
        RETURN e.name as name
        """
        async with self.driver.session() as session:
            result = await session.run(query, name=name, type=entity_type, props=props)
            record = await result.single()
            return record["name"] if record else ""

    async def save_relationship(
        self,
        from_name: str | None = None,
        from_type: str = "Entity",
        to_name: str | None = None,
        to_type: str = "Entity",
        rel_type: str | None = None,
        properties: dict | None = None,
        from_id: str | None = None,
        to_id: str | None = None,
        relationship_type: str | None = None,
    ):
        """Create a relationship between two entities."""
        from_name = from_name or from_id or ""
        to_name = to_name or to_id or ""
        rel_type = rel_type or relationship_type or "RELATED_TO"

        if not self._connected:
            return True

        props = properties or {}
        query = f"""
        MERGE (a:Entity {{name: $from_name, type: $from_type}})
        MERGE (b:Entity {{name: $to_name, type: $to_type}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $props
        RETURN type(r) as rel_type
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                from_name=from_name,
                from_type=from_type,
                to_name=to_name,
                to_type=to_type,
                props=props,
            )
        return True

    async def save_memory(
        self,
        content: str,
        category: str = "general",
        entities: list[str] | None = None,
        metadata: dict | None = None,
    ) -> int:
        """Save a memory node and link it to entities."""
        if not self._connected:
            return 0

        import time

        props = {
            "content": content,
            "category": category,
            "created_at": time.time(),
            **(metadata or {}),
        }

        query = """
        CREATE (m:Memory $props)
        RETURN id(m) as id
        """
        async with self.driver.session() as session:
            result = await session.run(query, props=props)
            record = await result.single()
            memory_id = record["id"] if record else 0

            # Link to entities
            if entities and memory_id:
                for entity_name in entities:
                    link_query = """
                    MATCH (m:Memory) WHERE id(m) = $mid
                    MERGE (e:Entity {name: $ename})
                    MERGE (m)-[:MENTIONS]->(e)
                    """
                    await session.run(link_query, mid=memory_id, ename=entity_name)

            return memory_id

    async def search(
        self,
        query: str = "",
        entity_type: str | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Search the knowledge graph."""
        if not self._connected:
            return []

        results = []

        if query:
            # Full-text search on memory content
            cypher = """
            MATCH (m:Memory)
            WHERE toLower(m.content) CONTAINS toLower($query)
            RETURN m.content as content, m.category as category,
                   m.created_at as created_at, id(m) as id
            ORDER BY m.created_at DESC
            LIMIT $limit
            """
            async with self.driver.session() as session:
                result = await session.run(cypher, query=query, limit=limit)
                records = await result.data()
                for r in records:
                    r["score"] = 0.8
                    r["source"] = "neo4j"
                    results.append(r)

        if entity_type:
            cypher = """
            MATCH (e:Entity {type: $type})
            RETURN e.name as name, e.type as type, properties(e) as props
            LIMIT $limit
            """
            async with self.driver.session() as session:
                result = await session.run(cypher, type=entity_type, limit=limit)
                records = await result.data()
                results.extend(records)

        return results

    async def get_related(
        self,
        entity_name: str,
        depth: int = 2,
        limit: int = 20,
    ) -> list[dict]:
        """Get entities related to a given entity up to N hops."""
        if not self._connected:
            return []

        cypher = f"""
        MATCH path = (e:Entity {{name: $name}})-[*1..{depth}]-(related)
        RETURN DISTINCT related.name as name, related.type as type,
               length(path) as distance,
               [r in relationships(path) | type(r)] as rel_types
        LIMIT $limit
        """
        async with self.driver.session() as session:
            result = await session.run(cypher, name=entity_name, limit=limit)
            return await result.data()

    async def get_entity_context(self, entity_name: str) -> str:
        """Get a natural language summary of an entity and its relationships."""
        if not self._connected:
            return f"Neo4j not connected. Cannot look up '{entity_name}'."

        related = await self.get_related(entity_name, depth=2, limit=15)
        if not related:
            return f"No knowledge graph data found for '{entity_name}'."

        lines = [f"Knowledge graph for '{entity_name}':"]
        for r in related:
            name = r.get("name", "?")
            rtype = r.get("type", "?")
            rels = " → ".join(r.get("rel_types", []))
            dist = r.get("distance", 0)
            lines.append(f"  {'  ' * dist}[{rtype}] {name} ({rels})")

        return "\n".join(lines)

    async def close(self):
        """Close the Neo4j driver."""
        if self.driver:
            await self.driver.close()
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected
