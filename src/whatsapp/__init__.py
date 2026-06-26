"""
WhatsApp Integration Package

Provides WhatsApp messaging capabilities via the Evolution API gateway.
"""

from src.whatsapp.client import WhatsAppClient
from src.whatsapp.webhook import router as whatsapp_router

__all__ = ["WhatsAppClient", "whatsapp_router"]
