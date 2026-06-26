from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ContextBuilder:
    def __init__(self, server):
        self.server = server

    def build_context(self, user_query: str) -> Dict[str, Any]:
        """
        Builds the context for the LLM based on the user's query.
        This is where we decide what information is relevant.
        """
        context = {
            "user_query": user_query,
            "relevant_emails": [],
            "calendar_availability": [],
            "user_profile": {} # To be implemented
        }
        
        # Simple keyword-based context fetching (can be improved with embeddings later)
        if "email" in user_query.lower() or "read" in user_query.lower():
            # context["relevant_emails"] = self.server.call_tool("list_recent_emails", {"limit": 5})
            pass
            
        if "calendar" in user_query.lower() or "schedule" in user_query.lower():
            # context["calendar_availability"] = self.server.call_tool("get_upcoming_events", {"days": 3})
            pass

        return context
