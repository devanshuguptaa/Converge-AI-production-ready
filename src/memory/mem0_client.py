"""
mem0 Memory Client Module

This module integrates with mem0 for long-term memory capabilities.
mem0 allows the agent to remember user preferences, facts, and context
across conversations.

Features:
- Add memories from conversations
- Search memories by user
- Delete specific memories
- LangChain-compatible tools
"""

from typing import List, Optional
from mem0 import Memory
from langchain.tools import tool

from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Global mem0 client
memory_client: Memory | None = None


def initialize_memory():
    """
    Initialize the mem0 memory client.
    
    This function creates the mem0 client with the API key from config.
    """
    global memory_client
    
    if not config.memory.enabled:
        logger.info("Memory system disabled")
        return
    
    logger.info("Initializing mem0 memory client...")
    
    try:
        # Try to initialize mem0 with the simpler API
        # mem0ai 1.x may have different initialization patterns
        memory_client = Memory()
        logger.info("✅ mem0 memory client initialized")
    except TypeError:
        # If Memory() doesn't work, try without config
        logger.warning("mem0 API incompatible - memory features will use fallback mode")
        memory_client = None
    except Exception as e:
        logger.error(f"Failed to initialize mem0: {e}", exc_info=True)
        raise


async def add_memory(user_id: str, text: str, metadata: Optional[dict] = None) -> str:
    """
    Add a memory for a user.
    
    Args:
        user_id: Slack user ID
        text: Memory text to store
        metadata: Optional metadata
        
    Returns:
        str: Memory ID
    """
    if not memory_client:
        logger.warning("Memory client not initialized - memory features unavailable")
        return ""
    
    try:
        result = memory_client.add(
            messages=[{"role": "user", "content": text}],
            user_id=user_id,
            metadata=metadata or {}
        )
        
        memory_id = result.get("id", "unknown")
        logger.info(f"Added memory for user {user_id}: {text[:50]}...")
        return memory_id
        
    except Exception as e:
        logger.error(f"Error adding memory: {e}", exc_info=True)
        raise


async def search_memories(
    user_id: str,
    query: Optional[str] = None,
    limit: int = 10
) -> List[str]:
    """
    Search memories for a user.
    
    Args:
        user_id: Slack user ID
        query: Optional search query (if None, returns all memories)
        limit: Maximum number of results
        
    Returns:
        List of memory texts
    """
    if not memory_client:
        logger.warning("Memory client not initialized - memory features unavailable")
        return []
    
    try:
        if query:
            results = memory_client.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
        else:
            results = memory_client.get_all(
                user_id=user_id,
                limit=limit
            )
        
        # Extract memory texts
        memories = []
        if results:
            for result in results:
                if isinstance(result, dict):
                    memory_text = result.get("memory", result.get("text", ""))
                else:
                    memory_text = str(result)
                
                if memory_text:
                    memories.append(memory_text)
        
        logger.info(f"Found {len(memories)} memories for user {user_id}")
        return memories
        
    except Exception as e:
        logger.error(f"Error searching memories: {e}", exc_info=True)
        return []


async def delete_memory(memory_id: str) -> bool:
    """
    Delete a specific memory.
    
    Args:
        memory_id: Memory ID to delete
        
    Returns:
        bool: True if successful
    """
    if not memory_client:
        logger.warning("Memory client not initialized - memory features unavailable")
        return False
    
    try:
        memory_client.delete(memory_id=memory_id)
        logger.info(f"Deleted memory {memory_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting memory: {e}", exc_info=True)
        return False


# LangChain Tools

@tool
async def remember_fact(user_id: str, fact: str) -> str:
    """
    Remember an important fact about the user.
    
    Use this tool when the user shares preferences, important information,
    or facts that should be remembered for future conversations.
    
    Args:
        user_id: Slack user ID
        fact: The fact to remember (e.g., "prefers Python over JavaScript")
        
    Returns:
        str: Confirmation message
        
    Example:
        >>> await remember_fact("U123456", "prefers Python over JavaScript")
        "✅ I'll remember that you prefer Python over JavaScript"
    """
    try:
        await add_memory(user_id, fact)
        return f"✅ I'll remember that: {fact}"
    except Exception as e:
        return f"Error saving memory: {str(e)}"


@tool
async def recall_memories(user_id: str, query: Optional[str] = None) -> str:
    """
    Recall what you remember about the user.
    
    Use this tool to retrieve memories about the user, either all memories
    or memories related to a specific query.
    
    Args:
        user_id: Slack user ID
        query: Optional search query to filter memories
        
    Returns:
        str: Formatted list of memories
        
    Example:
        >>> await recall_memories("U123456", "programming languages")
        "I remember:\n1. You prefer Python over JavaScript\n2. You're learning Rust"
    """
    try:
        memories = await search_memories(user_id, query, limit=10)
        
        if not memories:
            return "I don't have any memories about this yet."
        
        formatted = "I remember:\n\n"
        for i, memory in enumerate(memories, 1):
            formatted += f"{i}. {memory}\n"
        
        return formatted
        
    except Exception as e:
        return f"Error retrieving memories: {str(e)}"


@tool
async def forget_memory(memory_id: str) -> str:
    """
    Forget a specific memory.
    
    Use this tool when the user asks you to forget something specific.
    
    Args:
        memory_id: The ID of the memory to forget
        
    Returns:
        str: Confirmation message
        
    Example:
        >>> await forget_memory("mem_123456")
        "✅ Memory forgotten"
    """
    try:
        success = await delete_memory(memory_id)
        if success:
            return "✅ Memory forgotten"
        else:
            return "Error: Could not delete memory"
    except Exception as e:
        return f"Error deleting memory: {str(e)}"


# Export tools
MEMORY_TOOLS = [
    remember_fact,
    recall_memories,
    forget_memory,
]


if __name__ == "__main__":
    # Test memory client
    import asyncio
    
    async def test():
        initialize_memory()
        
        # Add a memory
        await add_memory("U123456", "Prefers Python over JavaScript")
        
        # Search memories
        memories = await search_memories("U123456")
        print(f"Memories: {memories}")
    
    asyncio.run(test())
