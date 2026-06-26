"""
Slack Application Module

This module initializes and manages the Slack Bolt application.
It handles all Slack events (messages, mentions, commands) and routes them
to the appropriate handlers.

Features:
- Socket Mode for real-time events
- Message event handling
- App mention handling
- Special commands (/help, /summarize, /reset)
- Typing indicators
- Reaction management
"""

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from src.config import config
from src.utils.logger import get_logger
from src.database import get_or_create_session, add_message, get_session_history, clear_session

logger = get_logger(__name__)

# Global Slack app instance
slack_app: AsyncApp | None = None
socket_handler: AsyncSocketModeHandler | None = None


async def initialize_slack_app() -> AsyncApp:
    """
    Initialize the Slack Bolt application.
    
    This function creates the Slack app instance and registers all event handlers.
    It uses Socket Mode for real-time event delivery without needing a public URL.
    
    Returns:
        AsyncApp: Initialized Slack Bolt application
    """
    global slack_app, socket_handler
    
    logger.info("Initializing Slack Bolt app...")
    
    # Create Slack app with Socket Mode
    slack_app = AsyncApp(
        token=config.slack.bot_token,
        signing_secret=config.slack.signing_secret
    )
    
    # Register event handlers
    register_event_handlers(slack_app)
    
    # Create Socket Mode handler
    socket_handler = AsyncSocketModeHandler(
        slack_app,
        config.slack.app_token
    )
    
    # Start Socket Mode handler in background
    await socket_handler.connect_async()
    
    logger.info("✅ Slack app initialized and connected")
    
    return slack_app


def register_event_handlers(app: AsyncApp) -> None:
    """
    Register all Slack event handlers.
    
    This function sets up listeners for:
    - Direct messages
    - App mentions in channels
    - Special commands
    
    Args:
        app: Slack Bolt application instance
    """
    
    @app.event("message")
    async def handle_message(event, say, client):
        """
        Handle direct message events.
        
        This is triggered when someone sends a DM to the bot.
        
        Args:
            event: Slack message event
            say: Function to send a response
            client: Slack Web API client
        """
        # Ignore bot messages and message changes
        if event.get("subtype") is not None:
            return
        
        user_id = event.get("user")
        channel_id = event.get("channel")
        text = event.get("text", "")
        thread_ts = event.get("thread_ts")
        
        logger.info(f"Received DM from user {user_id}: {text[:50]}...")
        
        # Check DM policy
        if not is_dm_allowed(user_id):
            await say(
                "Sorry, I'm not configured to accept DMs from all users. "
                "Please contact your workspace admin.",
                thread_ts=thread_ts
            )
            return
        
        # Handle special commands
        if await handle_special_command(text, user_id, channel_id, say, thread_ts):
            return
        
        # Process with AI agent
        await process_user_message(
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            text=text,
            say=say,
            client=client
        )
    
    @app.event("app_mention")
    async def handle_mention(event, say, client):
        """
        Handle app mention events.
        
        This is triggered when someone mentions the bot in a channel.
        
        Args:
            event: Slack mention event
            say: Function to send a response
            client: Slack Web API client
        """
        user_id = event.get("user")
        channel_id = event.get("channel")
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event.get("ts")
        
        # Remove bot mention from text
        text = remove_bot_mention(text)
        
        logger.info(f"Mentioned in channel {channel_id} by {user_id}: {text[:50]}...")
        
        # Handle special commands
        if await handle_special_command(text, user_id, channel_id, say, thread_ts):
            return
        
        # Process with AI agent
        await process_user_message(
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            text=text,
            say=say,
            client=client
        )
    
    logger.info("Event handlers registered")


def is_dm_allowed(user_id: str) -> bool:
    """
    Check if DMs are allowed from this user based on DM policy.
    
    Args:
        user_id: Slack user ID
        
    Returns:
        bool: True if DMs are allowed
    """
    if config.dm_policy == "open":
        return True
    elif config.dm_policy == "allowlist":
        return user_id in config.allowed_users
    else:  # pairing
        # For pairing mode, check if user has an active session
        # This is a simplified implementation
        return True


def remove_bot_mention(text: str) -> str:
    """
    Remove bot mention from message text.
    
    Slack mentions look like: <@U12345> hello
    This function removes the mention to get just the message.
    
    Args:
        text: Original message text with mention
        
    Returns:
        str: Text with mention removed
    """
    import re
    # Remove <@USERID> pattern
    text = re.sub(r'<@[A-Z0-9]+>', '', text)
    return text.strip()


async def handle_special_command(
    text: str,
    user_id: str,
    channel_id: str,
    say,
    thread_ts: str | None
) -> bool:
    """
    Handle special bot commands.
    
    Special commands:
    - /help or help - Show help message
    - /reset or reset - Clear conversation history
    - summarize or tldr - Summarize thread (if in thread)
    
    Args:
        text: Message text
        user_id: Slack user ID
        channel_id: Slack channel ID
        say: Function to send response
        thread_ts: Thread timestamp (if in thread)
        
    Returns:
        bool: True if command was handled, False otherwise
    """
    text_lower = text.lower().strip()
    
    # Help command
    if text_lower in ["/help", "help", "?"]:
        help_text = """
*Slack AI Assistant Help* 🤖

*Basic Usage:*
• Send me a DM or mention me in a channel
• I can answer questions, search Slack history, and help with tasks

*Special Commands:*
• `help` - Show this help message
• `reset` - Clear conversation history
• `summarize` or `tldr` - Summarize this thread

*Features:*
• 📚 Search Slack message history
• 💾 Remember your preferences
• 🔧 Create GitHub issues
• 📝 Create Notion pages
• ⏰ Set reminders and schedule messages

*Examples:*
• "What did we discuss about the new feature?"
• "Remember that I prefer Python"
• "Create a GitHub issue for the login bug"
• "Remind me tomorrow at 10am to review the PR"
"""
        await say(help_text, thread_ts=thread_ts)
        return True
    
    # Reset command
    if text_lower in ["/reset", "reset", "clear"]:
        session_id = get_or_create_session(user_id, channel_id, thread_ts)
        clear_session(session_id)
        await say(
            "✅ Conversation history cleared! Starting fresh.",
            thread_ts=thread_ts
        )
        return True
    
    # Summarize command (only in threads)
    if text_lower in ["summarize", "tldr", "summary"] and thread_ts:
        await say(
            "📝 Summarizing this thread...",
            thread_ts=thread_ts
        )
        # TODO: Implement thread summarization
        # This will be handled by the AI agent
        return False  # Let agent handle it
    
    return False


async def process_user_message(
    user_id: str,
    channel_id: str,
    thread_ts: str | None,
    text: str,
    say,
    client
) -> None:
    """
    Process a user message with the AI agent.
    
    This function:
    1. Gets or creates a session
    2. Adds user message to history
    3. Shows typing indicator
    4. Calls AI agent
    5. Sends response
    6. Adds assistant response to history
    
    Args:
        user_id: Slack user ID
        channel_id: Slack channel ID
        thread_ts: Thread timestamp (if in thread)
        text: User message text
        say: Function to send response
        client: Slack Web API client
    """
    try:
        # Get or create session
        session_id = get_or_create_session(user_id, channel_id, thread_ts)
        
        # Add user message to history
        add_message(session_id, "user", text)
        
        # Add "eyes" reaction to show we're processing
        try:
            await client.reactions_add(
                channel=channel_id,
                timestamp=thread_ts or "latest",
                name="eyes"
            )
        except Exception:
            pass  # Ignore reaction errors
        
        # Get session history
        history = get_session_history(session_id)
        
        # Call AI agent
        logger.info(f"Processing message for session {session_id}")
        
        # TODO: Import and call the actual agent
        # For now, placeholder response
        from src.agent.core import process_message
        response = await process_message(
            user_message=text,
            session_id=session_id,
            user_id=user_id,
            channel_id=channel_id,
            history=history
        )
        
        # Remove "eyes" reaction
        try:
            await client.reactions_remove(
                channel=channel_id,
                timestamp=thread_ts or "latest",
                name="eyes"
            )
        except Exception:
            pass
        
        # Send response (ensure it's not empty)
        if not response or not response.strip():
            response = "I processed your request, but I don't have anything specific to say. How else can I help?"
        
        await say(response, thread_ts=thread_ts)
        
        # Add assistant response to history
        add_message(session_id, "assistant", response)
        
        logger.info(f"Response sent for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await say(
            "Sorry, I encountered an error processing your message. Please try again.",
            thread_ts=thread_ts
        )


async def handle_slack_event(body: bytes, headers: dict) -> dict:
    """
    Handle incoming Slack event from webhook.
    
    This function is called by the FastAPI endpoint to process Slack events.
    
    Args:
        body: Request body (bytes)
        headers: Request headers
        
    Returns:
        dict: Response with status, body, and headers
    """
    if not slack_app:
        raise RuntimeError("Slack app not initialized")
    
    # The Socket Mode handler processes events automatically
    # This endpoint is mainly for health checks
    return {
        "status": 200,
        "body": "OK",
        "headers": {}
    }


if __name__ == "__main__":
    # Test Slack app initialization
    import asyncio
    
    async def test():
        app = await initialize_slack_app()
        logger.info("Slack app test successful!")
        await asyncio.sleep(5)
    
    asyncio.run(test())
