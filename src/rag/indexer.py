"""
Background Message Indexer

This module runs a background task that periodically fetches new Slack messages
and indexes them in the vector store for RAG.

The indexer runs on a schedule (default: every hour) and processes messages
from all channels the bot has access to.
"""

from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import config
from src.utils.logger import get_logger
from src.rag.vectorstore import add_messages

logger = get_logger(__name__)

# Global scheduler and Slack client
indexer_scheduler = None
slack_client = None


def set_slack_client(client):
    """
    Set the Slack client for the indexer to use.
    
    Args:
        client: Slack Web API client
    """
    global slack_client
    slack_client = client


async def index_channel_messages(channel_id: str, hours_back: int = 24):
    """
    Index messages from a specific channel.
    
    This function:
    1. Fetches recent messages from the channel
    2. Generates embeddings
    3. Stores them in the vector store
    
    Args:
        channel_id: Slack channel ID
        hours_back: How many hours of history to index (default: 24)
    """
    if not slack_client:
        logger.error("Slack client not set for indexer")
        return
    
    try:
        # Calculate oldest timestamp
        oldest_time = datetime.now() - timedelta(hours=hours_back)
        oldest_ts = oldest_time.timestamp()
        
        # Fetch messages from Slack
        response = await slack_client.conversations_history(
            channel=channel_id,
            oldest=str(oldest_ts),
            limit=1000  # Max per request
        )
        
        messages = response.get("messages", [])
        
        if not messages:
            logger.debug(f"No new messages in channel {channel_id}")
            return
        
        # Filter out bot messages and format for vector store
        formatted_messages = []
        for msg in messages:
            # Skip bot messages and system messages
            if msg.get("subtype") is not None:
                continue
            
            text = msg.get("text", "")
            if not text:
                continue
            
            formatted_messages.append({
                "text": text,
                "user": msg.get("user", "Unknown"),
                "timestamp": msg.get("ts", "")
            })
        
        if formatted_messages:
            # Add to vector store
            add_messages(formatted_messages, channel_id)
            logger.info(f"Indexed {len(formatted_messages)} messages from channel {channel_id}")
        
    except Exception as e:
        logger.error(f"Error indexing channel {channel_id}: {e}", exc_info=True)


async def index_all_channels():
    """
    Index messages from all channels the bot has access to.
    
    This is the main indexing function that runs on a schedule.
    """
    if not slack_client:
        logger.error("Slack client not set for indexer")
        return
    
    logger.info("Starting background message indexing...")
    
    try:
        # Get list of channels
        response = await slack_client.conversations_list(
            types="public_channel,private_channel",
            limit=1000
        )
        
        channels = response.get("channels", [])
        
        logger.info(f"Found {len(channels)} channels to index")
        
        # Index each channel
        for channel in channels:
            channel_id = channel.get("id")
            channel_name = channel.get("name", "unknown")
            
            # Check if bot is a member
            is_member = channel.get("is_member", False)
            if not is_member:
                logger.debug(f"Skipping channel #{channel_name} (not a member)")
                continue
            
            logger.info(f"Indexing channel #{channel_name}...")
            await index_channel_messages(channel_id, hours_back=config.rag.indexer_interval_minutes // 60)
        
        logger.info("✅ Background indexing complete")
        
    except Exception as e:
        logger.error(f"Error in background indexing: {e}", exc_info=True)


def start_indexer():
    """
    Start the background indexer scheduler.
    
    This function sets up a periodic task that indexes new messages
    based on the configured interval.
    """
    global indexer_scheduler
    
    if not config.rag.enabled:
        logger.info("RAG disabled, skipping indexer")
        return
    
    logger.info("Starting background message indexer...")
    
    # Create scheduler
    indexer_scheduler = AsyncIOScheduler()
    
    # Schedule indexing job
    indexer_scheduler.add_job(
        index_all_channels,
        'interval',
        minutes=config.rag.indexer_interval_minutes,
        id='slack_message_indexer',
        replace_existing=True
    )
    
    # Run once immediately
    indexer_scheduler.add_job(
        index_all_channels,
        'date',
        run_date=datetime.now() + timedelta(seconds=30),  # Wait 30s for startup
        id='initial_index'
    )
    
    # Start scheduler
    indexer_scheduler.start()
    
    logger.info(f"✅ Indexer scheduled to run every {config.rag.indexer_interval_minutes} minutes")


def stop_indexer():
    """
    Stop the background indexer scheduler.
    """
    global indexer_scheduler
    
    if indexer_scheduler:
        indexer_scheduler.shutdown()
        logger.info("Background indexer stopped")


if __name__ == "__main__":
    # Test indexer
    import asyncio
    
    async def test():
        # This would need a real Slack client
        logger.info("Indexer test - would need real Slack client")
    
    asyncio.run(test())
