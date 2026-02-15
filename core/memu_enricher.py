"""
iTaK MemU Enricher - Routes extracted facts to existing memory stores.

This module processes MemU extraction responses and stores facts in:
- SQLite (with source="memu" tag)
- Neo4j (if enabled, with source="memu")
- Optional MEMORY.md append for audit trail
"""

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MemUEnricher:
    """Processes MemU extractions and routes to iTaK memory layers."""

    def __init__(self, memory_manager, config: dict):
        """Initialize enricher.
        
        Args:
            memory_manager: iTaK MemoryManager instance
            config: MemU config dict
        """
        self.memory = memory_manager
        self.config = config
        self.memu_weight = config.get("memu_weight", 0.8)
        self.append_to_memory_md = config.get("append_to_memory_md", True)

    async def process_extraction(self, memu_response: dict) -> list[int]:
        """Process MemU extraction response and store facts.
        
        Args:
            memu_response: Response from MemU memorize endpoint
            
        Returns:
            List of memory IDs for stored facts
        """
        if not memu_response:
            return []
        
        # Extract facts from response
        # Expected format: {"facts": [...], "entities": [...], "metadata": {...}}
        facts = memu_response.get("facts", [])
        entities = memu_response.get("entities", [])
        response_metadata = memu_response.get("metadata", {})
        
        if not facts and not isinstance(facts, list):
            logger.debug("MemU: no facts in response")
            return []
        
        stored_ids = []
        
        # Process each extracted fact
        for fact in facts:
            # Handle different fact formats
            if isinstance(fact, str):
                content = fact
                fact_metadata = {}
                fact_entities = []
            elif isinstance(fact, dict):
                content = fact.get("content", "") or fact.get("text", "")
                fact_metadata = fact.get("metadata", {})
                fact_entities = fact.get("entities", [])
            else:
                logger.warning(f"MemU: unknown fact format: {type(fact)}")
                continue
            
            if not content:
                continue
            
            # Merge metadata
            metadata = {
                **response_metadata,
                **fact_metadata,
                "memu_weight": self.memu_weight,
                "extraction_source": "memu",
            }
            
            # Determine category
            category = fact_metadata.get("category", "memu-fact")
            
            # Combine entities
            all_entities = list(set(entities + fact_entities))
            
            try:
                # Save to existing stores via MemoryManager
                memory_id = await self.memory.save(
                    content=content,
                    category=category,
                    metadata=metadata,
                    source="memu",
                    entities=all_entities if all_entities else None,
                )
                stored_ids.append(memory_id)
                logger.info(f"MemU: stored fact #{memory_id} to memory")
                
            except Exception as e:
                logger.error(f"MemU: failed to store fact: {e}")
        
        # Optional: Append to MEMORY.md for audit trail
        if self.append_to_memory_md and facts:
            try:
                await self._append_to_memory_md(facts)
            except Exception as e:
                logger.warning(f"MemU: failed to append to MEMORY.md: {e}")
        
        logger.info(f"MemU: processed {len(stored_ids)} facts from extraction")
        return stored_ids

    async def _append_to_memory_md(self, facts: list):
        """Append extracted facts to MEMORY.md for audit trail."""
        memory_md = Path("memory/MEMORY.md")
        
        if not memory_md.exists():
            logger.debug("MemU: MEMORY.md not found, skipping append")
            return
        
        # Format facts for markdown
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        lines = [f"\n## MemU Extraction - {timestamp}\n"]
        for fact in facts:
            if isinstance(fact, str):
                content = fact
            elif isinstance(fact, dict):
                content = fact.get("content", "") or fact.get("text", "")
            else:
                continue
            
            if content:
                lines.append(f"- {content}\n")
        
        # Append atomically
        try:
            with open(memory_md, "a", encoding="utf-8") as f:
                f.writelines(lines)
            logger.debug(f"MemU: appended {len(facts)} facts to MEMORY.md")
        except Exception as e:
            logger.warning(f"MemU: error writing to MEMORY.md: {e}")
