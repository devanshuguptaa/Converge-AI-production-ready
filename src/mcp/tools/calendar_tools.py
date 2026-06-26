from typing import Dict, Any
from ..integrations.calendar.reader import CalendarReader
from ..integrations.calendar.writer import CalendarWriter
from ..integrations.calendar.service import CalendarService
from ..core.permissions import PermissionManager, MCPScope

class CalendarTools:
    def __init__(self, permission_manager: PermissionManager, client_secret_path: str, token_path: str = 'token_calendar.pickle'):
        self.permission_manager = permission_manager
        self.service = CalendarService(client_secret_path, token_path=token_path)
        self.reader = CalendarReader(self.service)
        self.writer = CalendarWriter(self.service)

    def get_tools(self) -> Dict[str, Any]:
        return {
            "list_calendar_events": self.list_calendar_events_tool(),
            "create_calendar_event": self.create_calendar_event_tool()
        }

    def list_calendar_events_tool(self):
        def run(start_time: str = None, end_time: str = None):
            self.permission_manager.validate_tool_access("list_calendar_events", MCPScope.CALENDAR_READ)
            return self.reader.list_events(start_time=start_time, end_time=end_time)

        return {
            "name": "list_calendar_events",
            "description": "Lists calendar events within a date range. If no dates provided, lists next 7 days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {"type": "string", "description": "Start time in ISO format (e.g. 2023-10-27T10:00:00Z)"},
                    "end_time": {"type": "string", "description": "End time in ISO format"}
                },
                "required": []
            },
            "run": run
        }

    def create_calendar_event_tool(self):
        def run(summary: str, start_time: str, end_time: str, description: str = None):
            self.permission_manager.validate_tool_access("create_calendar_event", MCPScope.CALENDAR_WRITE)
            return self.writer.create_event(summary, start_time, end_time, description)
        
        return {
            "name": "create_calendar_event",
            "description": "Creates a new calendar event.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Start time in ISO format (e.g. 2023-10-27T10:00:00Z)"},
                    "end_time": {"type": "string", "description": "End time in ISO format"},
                    "description": {"type": "string", "description": "Event description"}
                },
                "required": ["summary", "start_time", "end_time"]
            },
            "run": run
        }
