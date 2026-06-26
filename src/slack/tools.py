"""
Slack Tools Module

This module provides LangChain-compatible tools for Slack actions.
These tools allow the AI agent to interact with Slack (send messages,
get channel info, etc.).

All tools follow the LangChain tool format and can be used directly
with the agent.
"""

from typing import Optional
from langchain.tools import tool

from src.utils.logger import get_logger
from src.config import config

logger = get_logger(__name__)

# Global Slack client (will be set by slack app)
slack_client = None


def set_slack_client(client):
    """
    Set the global Slack client for tools to use.
    
    This should be called during Slack app initialization.
    
    Args:
        client: Slack Web API client
    """
    global slack_client
    slack_client = client


@tool
async def send_slack_message(channel_id: str, text: str, thread_ts: Optional[str] = None) -> str:
    """
    Send a message to a Slack channel or thread.
    
    Use this tool when you need to send a message to a specific channel
    or reply to a thread.
    
    Args:
        channel_id: The Slack channel ID (e.g., C1234567890)
        text: The message text to send
        thread_ts: Optional thread timestamp to reply in a thread
        
    Returns:
        str: Confirmation message with timestamp
        
    Example:
        >>> await send_slack_message("C1234567890", "Hello team!")
        "Message sent successfully at 1234567890.123456"
    """
    if not slack_client:
        return "Error: Slack client not initialized"
    
    try:
        response = await slack_client.chat_postMessage(
            channel=channel_id,
            text=text,
            thread_ts=thread_ts
        )
        
        ts = response["ts"]
        logger.info(f"Sent message to {channel_id}: {text[:50]}...")
        return f"Message sent successfully at {ts}"
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return f"Error sending message: {str(e)}"


@tool
async def get_channel_history(
    channel_id: str,
    limit: int = 10,
    oldest: Optional[str] = None
) -> str:
    """
    Get recent messages from a Slack channel.
    
    Use this tool to retrieve conversation history from a channel.
    Useful for understanding context or finding information.
    
    Args:
        channel_id: The Slack channel ID
        limit: Number of messages to retrieve (default: 10, max: 100)
        oldest: Only messages after this timestamp
        
    Returns:
        str: Formatted message history
        
    Example:
        >>> await get_channel_history("C1234567890", limit=5)
        "Messages from #general:\n1. User1: Hello\n2. User2: Hi there..."
    """
    if not slack_client:
        return "Error: Slack client not initialized"
    
    try:
        response = await slack_client.conversations_history(
            channel=channel_id,
            limit=min(limit, 100),
            oldest=oldest
        )
        
        messages = response["messages"]
        
        if not messages:
            return "No messages found in this channel."
        
        # Format messages
        formatted = []
        for i, msg in enumerate(messages, 1):
            user = msg.get("user", "Unknown")
            text = msg.get("text", "")
            ts = msg.get("ts", "")
            formatted.append(f"{i}. <@{user}> ({ts}): {text}")
        
        return "\n".join(formatted)
        
    except Exception as e:
        logger.error(f"Error getting channel history: {e}")
        return f"Error getting channel history: {str(e)}"


@tool
async def list_channels() -> str:
    """
    List all public channels in the workspace.
    
    Use this tool to find channel IDs or see what channels are available.
    
    Returns:
        str: List of channels with IDs and names
        
    Example:
        >>> await list_channels()
        "Channels:\n1. #general (C1234567890)\n2. #random (C0987654321)..."
    """
    if not slack_client:
        return "Error: Slack client not initialized"
    
    try:
        response = await slack_client.conversations_list(
            types="public_channel",
            limit=100
        )
        
        channels = response["channels"]
        
        if not channels:
            return "No channels found."
        
        # Format channels
        formatted = []
        for i, channel in enumerate(channels, 1):
            name = channel.get("name", "unknown")
            channel_id = channel.get("id", "")
            formatted.append(f"{i}. #{name} ({channel_id})")
        
        return "Channels:\n" + "\n".join(formatted)
        
    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        return f"Error listing channels: {str(e)}"


@tool
async def get_user_info(user_id: str) -> str:
    """
    Get information about a Slack user.
    
    Use this tool to get user details like name, email, timezone, etc.
    
    Args:
        user_id: The Slack user ID (e.g., U1234567890)
        
    Returns:
        str: User information
        
    Example:
        >>> await get_user_info("U1234567890")
        "User: John Doe (@johndoe)\nEmail: john@example.com\nTimezone: America/New_York"
    """
    if not slack_client:
        return "Error: Slack client not initialized"
    
    try:
        response = await slack_client.users_info(user=user_id)
        user = response["user"]
        
        name = user.get("real_name", "Unknown")
        username = user.get("name", "unknown")
        email = user.get("profile", {}).get("email", "N/A")
        tz = user.get("tz", "N/A")
        
        return (
            f"User: {name} (@{username})\n"
            f"Email: {email}\n"
            f"Timezone: {tz}"
        )
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return f"Error getting user info: {str(e)}"


@tool
async def add_reaction(channel_id: str, timestamp: str, reaction: str) -> str:
    """
    Add an emoji reaction to a message.
    
    Use this tool to react to messages with emojis.
    
    Args:
        channel_id: The Slack channel ID
        timestamp: The message timestamp
        reaction: The emoji name (without colons, e.g., "thumbsup")
        
    Returns:
        str: Confirmation message
        
    Example:
        >>> await add_reaction("C1234567890", "1234567890.123456", "thumbsup")
        "Reaction :thumbsup: added successfully"
    """
    if not slack_client:
        return "Error: Slack client not initialized"
    
    try:
        await slack_client.reactions_add(
            channel=channel_id,
            timestamp=timestamp,
            name=reaction
        )
        
        logger.info(f"Added reaction :{reaction}: to message {timestamp}")
        return f"Reaction :{reaction}: added successfully"
        
    except Exception as e:
        logger.error(f"Error adding reaction: {e}")
        return f"Error adding reaction: {str(e)}"


# Export all tools as a list for easy registration
SLACK_TOOLS = [
    send_slack_message,
    get_channel_history,
    list_channels,
    get_user_info,
    add_reaction,
]


if __name__ == "__main__":
    # Test tool definitions
    print("Slack Tools:")
    for tool in SLACK_TOOLS:
        print(f"  - {tool.name}: {tool.description[:60]}...")
