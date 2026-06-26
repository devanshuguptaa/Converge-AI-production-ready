from typing import List, Dict, Any
from .service import CalendarService
import datetime
import logging

logger = logging.getLogger(__name__)

class CalendarReader:
    def __init__(self, calendar_service: CalendarService):
        self.service = calendar_service.get_service()

    def list_events(self, max_results: int = 10, start_time: str = None, end_time: str = None) -> List[Dict[str, Any]]:
        try:
            # Default to now if no start_time provided
            if not start_time:
                start_time = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
            
            # Default to 7 days from start_time if no end_time provided
            if not end_time:
                # Parse start_time to calculate end_time
                try:
                    start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                except ValueError:
                    # Fallback if parsing fails (e.g. if start_time was just generated above)
                    start_dt = datetime.datetime.utcnow()

                end_time = (start_dt + datetime.timedelta(days=7)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary', timeMin=start_time, timeMax=end_time,
                maxResults=max_results, singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])
            return events
        except Exception as e:
            return []
