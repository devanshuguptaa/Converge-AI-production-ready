from typing import Dict, Any
from .service import CalendarService
import logging

logger = logging.getLogger(__name__)

class CalendarWriter:
    def __init__(self, calendar_service: CalendarService):
        self.service = calendar_service.get_service()

    def create_event(self, summary: str, start_time: str, end_time: str, description: str = None) -> Dict[str, Any]:
        """
        Creates an event. Times must be in ISO format (e.g., '2023-10-27T10:00:00-07:00').
        """
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC', # Defaulting to UTC for simplicity, should be configurable
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }

        try:
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            logger.info(f"Event created: {event.get('htmlLink')}")
            return event
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise
