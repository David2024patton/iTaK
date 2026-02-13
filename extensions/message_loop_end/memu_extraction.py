"""
iTaK Extension: MemU Extraction - Runs at end of message loop.
Fires async enrichment after response (fire-and-forget).
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


async def execute(agent, **kwargs):
    """Fire MemU extraction asynchronously after response (non-blocking).
    
    This extension:
    1. Checks if MemU is enabled
    2. Grabs last N conversation turns
    3. Fires async task to send to MemU (doesn't block)
    4. MemU extracts facts and routes to existing stores
    """
    # Check if MemU is configured
    memu_config = agent.config.get("memory", {}).get("memu", {})
    if not memu_config.get("enabled", False):
        return
    
    # Get history
    if not hasattr(agent, "history") or not agent.history:
        return
    
    # Fire async task (fire-and-forget)
    asyncio.create_task(_enrich_with_memu(agent, agent.history))
    logger.debug("MemU: fired enrichment task (non-blocking)")


async def _enrich_with_memu(agent, history: list):
    """Async enrichment task - sends to MemU and stores extracted facts.
    
    This runs in background and doesn't block the agent loop.
    """
    try:
        # Lazy init MemU store and enricher
        if not hasattr(agent, "_memu_store"):
            from memory.memu_store import MemUStore
            memu_config = agent.config.get("memory", {}).get("memu", {})
            agent._memu_store = MemUStore(memu_config)
        
        if not hasattr(agent, "_memu_enricher"):
            from core.memu_enricher import MemUEnricher
            memu_config = agent.config.get("memory", {}).get("memu", {})
            agent._memu_enricher = MemUEnricher(agent.memory, memu_config)
        
        # Send to MemU for extraction
        memu_response = await agent._memu_store.memorize(
            messages=history,
            metadata={"agent_name": agent.config.get("agent", {}).get("name", "iTaK")},
        )
        
        if memu_response:
            # Process extraction and store facts
            stored_ids = await agent._memu_enricher.process_extraction(memu_response)
            if stored_ids:
                logger.info(f"MemU: enrichment complete - stored {len(stored_ids)} facts")
        
    except Exception as e:
        # Log error but don't crash - this is fire-and-forget
        logger.warning(f"MemU: enrichment error: {e}")
