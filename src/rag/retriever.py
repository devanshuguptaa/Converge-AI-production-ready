"""
RAG Retriever Module

This module provides LangChain-compatible tools for semantic search
across Slack message history.

The retriever uses the ChromaDB vector store to find relevant messages
based on semantic similarity to the query.
"""

from typing import List, Optional
from langchain.tools import tool

from src.utils.logger import get_logger
from src.rag.vectorstore import search_messages

logger = get_logger(__name__)


@tool
async def search_slack_history(
    query: str,
    channel_id: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Search through Slack message history using semantic search.
    
    Use this tool when users ask about past conversations, discussions,
    or information that was shared in Slack.
    
    This tool performs semantic search, meaning it finds messages that are
    conceptually similar to the query, not just keyword matches.
    
    Args:
        query: What to search for (e.g., "discussions about the new feature")
        channel_id: Optional channel ID to limit search to specific channel
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        str: Formatted search results with relevant messages
        
    Example:
        >>> await search_slack_history("what did we discuss about authentication?")
        "Found 3 relevant messages:\n1. @user1: We should implement OAuth2...\n2. @user2: The authentication flow needs..."
    """
    try:
        # Search vector store
        results = search_messages(
            query=query,
            channel_id=channel_id,
            limit=limit
        )
        
        if not results:
            return f"No relevant messages found for: {query}"
        
        # Format results
        formatted = f"Found {len(results)} relevant messages:\n\n"
        
        for i, result in enumerate(results, 1):
            user_id = result.get('user_id', 'Unknown')
            text = result.get('text', '')
            timestamp = result.get('timestamp', '')
            relevance = result.get('relevance', 0)
            
            formatted += f"{i}. <@{user_id}> (relevance: {relevance:.2f}):\n"
            formatted += f"   {text}\n"
            formatted += f"   (timestamp: {timestamp})\n\n"
        
        logger.info(f"Retrieved {len(results)} results for query: {query[:50]}...")
        return formatted
        
    except Exception as e:
        logger.error(f"Error searching Slack history: {e}", exc_info=True)
        return f"Error searching Slack history: {str(e)}"


# Export tools
RAG_TOOLS = [
    search_slack_history,
]


if __name__ == "__main__":
    # Test retriever
    import asyncio
    
    async def test():
        result = await search_slack_history(
            query="authentication feature",
            limit=5
        )
        print(result)
    
    asyncio.run(test())
