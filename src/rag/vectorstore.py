"""
ChromaDB Vector Store Module

This module manages the ChromaDB vector database for storing and retrieving
Slack message embeddings.

Features:
- Initialize and manage ChromaDB collections
- Store message embeddings with metadata
- Semantic search across messages
- Filter by channel, user, date range
"""

from pathlib import Path
from typing import Optional, List, Dict
import chromadb
from chromadb.config import Settings

from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Global ChromaDB client and collection
chroma_client = None
collection = None


async def initialize_vectorstore():
    """
    Initialize the ChromaDB vector store.
    
    This function:
    1. Creates the data directory if needed
    2. Initializes the ChromaDB client
    3. Creates or gets the collection for Slack messages
    
    The collection uses Gemini embeddings for semantic search.
    """
    global chroma_client, collection
    
    logger.info("Initializing ChromaDB vector store...")
    
    # Ensure data directory exists
    db_path = Path(config.rag.vector_db_path)
    db_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize ChromaDB client
    chroma_client = chromadb.PersistentClient(
        path=str(db_path),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    # Create or get collection
    # We'll use Gemini embeddings, so we need a custom embedding function
    from src.rag.embeddings import GeminiEmbeddingFunction
    
    embedding_function = GeminiEmbeddingFunction()
    
    collection = chroma_client.get_or_create_collection(
        name="slack_messages",
        embedding_function=embedding_function,
        metadata={"description": "Slack message history for RAG"}
    )
    
    # Get collection stats
    count = collection.count()
    logger.info(f"✅ ChromaDB initialized with {count} documents")


def add_messages(
    messages: List[Dict],
    channel_id: str
) -> None:
    """
    Add messages to the vector store.
    
    Args:
        messages: List of message dicts with keys:
            - id: Unique message ID
            - text: Message text
            - user: User ID
            - timestamp: Message timestamp
        channel_id: Slack channel ID
    """
    if not collection:
        raise RuntimeError("Vector store not initialized")
    
    if not messages:
        return
    
    # Prepare data for ChromaDB
    ids = []
    documents = []
    metadatas = []
    
    for msg in messages:
        # Create unique ID
        msg_id = f"{channel_id}_{msg['timestamp']}"
        ids.append(msg_id)
        
        # Document is the message text
        documents.append(msg['text'])
        
        # Metadata for filtering
        metadatas.append({
            "channel_id": channel_id,
            "user_id": msg['user'],
            "timestamp": msg['timestamp'],
            "type": "message"
        })
    
    # Add to collection
    try:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Added {len(messages)} messages to vector store")
    except Exception as e:
        logger.error(f"Error adding messages: {e}", exc_info=True)


def search_messages(
    query: str,
    channel_id: Optional[str] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Search for relevant messages using semantic search.
    
    Args:
        query: Search query
        channel_id: Optional channel ID to filter by
        limit: Maximum number of results
        
    Returns:
        List of matching messages with metadata
    """
    if not collection:
        raise RuntimeError("Vector store not initialized")
    
    # Build where filter
    where = None
    if channel_id:
        where = {"channel_id": channel_id}
    
    # Search
    try:
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where
        )
        
        # Format results
        formatted_results = []
        if results and results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0
                
                formatted_results.append({
                    "text": doc,
                    "channel_id": metadata.get("channel_id"),
                    "user_id": metadata.get("user_id"),
                    "timestamp": metadata.get("timestamp"),
                    "relevance": 1 - distance  # Convert distance to relevance score
                })
        
        logger.info(f"Found {len(formatted_results)} results for query: {query[:50]}...")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error searching messages: {e}", exc_info=True)
        return []


def delete_messages(channel_id: str) -> None:
    """
    Delete all messages from a specific channel.
    
    Args:
        channel_id: Slack channel ID
    """
    if not collection:
        raise RuntimeError("Vector store not initialized")
    
    try:
        # Get all IDs for this channel
        results = collection.get(
            where={"channel_id": channel_id}
        )
        
        if results and results['ids']:
            collection.delete(ids=results['ids'])
            logger.info(f"Deleted {len(results['ids'])} messages from channel {channel_id}")
    except Exception as e:
        logger.error(f"Error deleting messages: {e}", exc_info=True)


if __name__ == "__main__":
    # Test vector store
    import asyncio
    
    async def test():
        await initialize_vectorstore()
        
        # Add test messages
        test_messages = [
            {
                "id": "1",
                "text": "We should implement the new authentication feature",
                "user": "U123456",
                "timestamp": "1234567890.123456"
            },
            {
                "id": "2",
                "text": "The login bug needs to be fixed urgently",
                "user": "U789012",
                "timestamp": "1234567891.123456"
            }
        ]
        
        add_messages(test_messages, "C123456")
        
        # Search
        results = search_messages("authentication", limit=5)
        print(f"Search results: {results}")
    
    asyncio.run(test())
