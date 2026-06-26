from enum import Enum
from typing import List, Set

class MCPScope(Enum):
    # Gmail Scopes
    GMAIL_READ = "gmail.readonly"
    GMAIL_SEND = "gmail.send"
    GMAIL_MODIFY = "gmail.modify" # For labels, archiving
    
    # Calendar Scopes
    CALENDAR_READ = "calendar.readonly"
    CALENDAR_WRITE = "calendar.events"

class PermissionManager:
    def __init__(self, active_scopes: List[str]):
        self.active_scopes = set(active_scopes)

    def has_permission(self, required_scope: MCPScope) -> bool:
        """Checks if the active scopes include the required scope."""
        # In a real app, we might map broad scopes to specific ones.
        # For now, we assume direct mapping or simple logic.
        
        # Example: 'https://www.googleapis.com/auth/gmail.readonly'
        # We'll check if the enum value is contained in any active scope string
        return any(required_scope.value in scope for scope in self.active_scopes)

    def validate_tool_access(self, tool_name: str, required_scope: MCPScope):
        if not self.has_permission(required_scope):
            raise PermissionError(f"Tool '{tool_name}' requires scope '{required_scope.value}' which is not active.")
