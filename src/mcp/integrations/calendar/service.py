import os
import pickle
import contextvars
from typing import Any
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import logging
from src.utils.context import current_user_id, current_channel_id
from src.config import config
from src.mcp.integrations.gmail.service import (
    GoogleAuthRequiredError,
    GoogleServiceProxy,
)

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

# Request-scoped cache for the built Google Calendar service
_calendar_service_cache = contextvars.ContextVar("calendar_service_cache", default=None)


class CalendarService:
    def __init__(
        self,
        client_secret_path: str,
        token_path: str = "credentials/token_calendar.pickle",
    ):
        self.client_secret_path = client_secret_path
        self.token_path = token_path

    def get_token_path(self) -> str:
        user_id = current_user_id.get()
        channel_id = current_channel_id.get()
        if user_id and channel_id:
            os.makedirs("credentials", exist_ok=True)
            return f"credentials/token_calendar_{channel_id}_{user_id}.pickle"
        return self.token_path

    def authenticate(self) -> Any:
        creds = None
        token_path = self.get_token_path()

        if os.path.exists(token_path):
            with open(token_path, "rb") as token:
                try:
                    creds = pickle.load(token)
                except Exception as e:
                    logger.error(f"Error loading pickle {token_path}: {e}")

        # Attempt to refresh if credentials exist and are expired
        if creds and not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    with open(token_path, "wb") as token:
                        pickle.dump(creds, token)
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    creds = None

        if not creds or not creds.valid:
            user_id = current_user_id.get()
            channel_id = current_channel_id.get()
            if not user_id or not channel_id:
                # Fallback to general token_path if it exists and is valid
                if token_path != self.token_path and os.path.exists(self.token_path):
                    with open(self.token_path, "rb") as token:
                        creds = pickle.load(token)
                    if creds and creds.valid:
                        return build("calendar", "v3", credentials=creds)

                raise ValueError("No user context available for web OAuth flow")

            login_url = f"{config.redirect_uri_base}/auth/login?user_id={user_id}&channel_id={channel_id}&service=calendar"
            raise GoogleAuthRequiredError(service_name="Calendar", login_url=login_url)

        return build("calendar", "v3", credentials=creds)

    def get_service(self):
        def getter():
            cache = _calendar_service_cache.get()
            if cache is not None:
                return cache
            service_instance = self.authenticate()
            _calendar_service_cache.set(service_instance)
            return service_instance

        return GoogleServiceProxy(getter)
