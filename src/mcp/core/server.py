import os
import logging
from typing import Dict, Any, List
from .permissions import PermissionManager, MCPScope

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPServer:
    def __init__(self, credentials_path_gmail: str, credentials_path_calendar: str):
        self.credentials_path_gmail = credentials_path_gmail
        self.credentials_path_calendar = credentials_path_calendar
        self.tools: Dict[str, Any] = {}
        self.permission_manager = None
        self.context = {}
        
        # Initialize components
        self._initialize_permissions()
        self._register_tools()
        
        # Lock for thread safety during tool execution
        import threading
        self.lock = threading.Lock()
        
    def _initialize_permissions(self):
        # In a real scenario, we'd load these from the authenticated session
        # For this demo, we assume we have full access if credentials exist
        # This is a simplification.
        scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events"
        ]
        self.permission_manager = PermissionManager(scopes)
        logger.info("Permissions initialized.")

    def _register_tools(self):
        """Registers all available tools."""
        from ..tools.email_tools import EmailTools
        from ..tools.calendar_tools import CalendarTools
        
        email_tools = EmailTools(self.permission_manager, self.credentials_path_gmail)
        calendar_tools = CalendarTools(self.permission_manager, self.credentials_path_calendar)
        
        self.tools.update(email_tools.get_tools())
        self.tools.update(calendar_tools.get_tools())
        logger.info("Tools registered.")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns a list of available tools and their schemas."""
        return [tool.schema for tool in self.tools.values()]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Executes a tool call."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found.")
        
        tool = self.tools[tool_name]
        logger.info(f"Executing tool: {tool_name}")
        
        try:
            # Acquire lock to ensure thread safety for API clients (httplib2 is not thread-safe)
            with self.lock:
                return tool["run"](**arguments)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            raise

    def get_context(self) -> Dict[str, Any]:
        """Builds and returns the current context."""
        # This will use the ContextBuilder
        return self.context
