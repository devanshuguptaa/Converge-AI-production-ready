"""
Email & Calendar MCP Tools

This module provides LangChain-compatible tools for Gmail and Calendar integration.
"""

from langchain_core.tools import StructuredTool
import os

# Import the Email MCP modules
from src.mcp.tools.email_tools import EmailTools
from src.mcp.tools.calendar_tools import CalendarTools
from src.mcp.core.permissions import PermissionManager, MCPScope


# Initialize Email & Calendar tools
def get_email_calendar_tools():
    """Get LangChain-compatible email and calendar tools"""

    # Resolve Gmail credentials path
    gmail_creds_path = os.getenv("GMAIL_CREDENTIALS_PATH")
    if not gmail_creds_path:
        default_gmail = "credentials/client_secret_gmail.json"
        combined = "credentials/client_secret_for_gmail_and_calender.json"
        gmail_creds_path = default_gmail if os.path.exists(default_gmail) else combined

    # Resolve Calendar credentials path
    calendar_creds_path = os.getenv("CALENDAR_CREDENTIALS_PATH")
    if not calendar_creds_path:
        default_calendar = "credentials/client_secret_calendar.json"
        combined = "credentials/client_secret_for_gmail_and_calender.json"
        calendar_creds_path = (
            default_calendar if os.path.exists(default_calendar) else combined
        )

    # Get token paths from config or env
    gmail_token_path = os.getenv("GMAIL_TOKEN_PATH", "credentials/token_gmail.pickle")
    calendar_token_path = os.getenv(
        "CALENDAR_TOKEN_PATH", "credentials/token_calendar.pickle"
    )

    # Initialize permission manager with all required scopes
    # In a real app, these would come from the authenticated user's token
    active_scopes = [
        MCPScope.GMAIL_READ.value,
        MCPScope.GMAIL_SEND.value,
        MCPScope.CALENDAR_READ.value,
        MCPScope.CALENDAR_WRITE.value,
    ]
    permission_manager = PermissionManager(active_scopes)

    # Create email and calendar tool instances
    email_tools_instance = EmailTools(
        permission_manager, gmail_creds_path, token_path=gmail_token_path
    )
    calendar_tools_instance = CalendarTools(
        permission_manager, calendar_creds_path, token_path=calendar_token_path
    )

    # Get raw tool dictionaries
    email_raw_tools = email_tools_instance.get_tools()
    calendar_raw_tools = calendar_tools_instance.get_tools()

    # Convert to LangChain StructuredTools
    langchain_tools = []

    # Email tools
    for tool_name, tool_def in email_raw_tools.items():
        langchain_tools.append(
            StructuredTool.from_function(
                func=tool_def["run"],
                name=tool_def["name"],
                description=tool_def["description"],
            )
        )

    # Calendar tools
    for tool_name, tool_def in calendar_raw_tools.items():
        langchain_tools.append(
            StructuredTool.from_function(
                func=tool_def["run"],
                name=tool_def["name"],
                description=tool_def["description"],
            )
        )

    return langchain_tools


# Export individual tools for easier imports
EMAIL_CALENDAR_TOOLS = []

try:
    EMAIL_CALENDAR_TOOLS = get_email_calendar_tools()
except Exception as e:
    # If initialization fails (e.g., missing credentials), log and continue
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to initialize email/calendar tools: {e}")
    logger.warning("Email and calendar features will not be available")
