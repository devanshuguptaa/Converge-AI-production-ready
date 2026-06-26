from typing import Dict, Any
from .service import GmailService
import base64
from email.mime.text import MIMEText
import logging

logger = logging.getLogger(__name__)

import html

class GmailSender:
    def __init__(self, gmail_service: GmailService):
        self.service = gmail_service.get_service()

    def create_message(self, sender: str, to: str, subject: str, message_text: str) -> Dict[str, Any]:
        # Sanitize the message text to prevent XSS/malicious HTML
        # This converts characters like <, >, & to HTML entities (&lt;, &gt;, &amp;)
        safe_message_text = html.escape(message_text)
        
        message = MIMEText(safe_message_text)
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw}

    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        try:
            # In a real app, we'd get the authenticated user's email
            sender = "me" 
            message = self.create_message(sender, to, subject, body)
            sent_message = self.service.users().messages().send(userId='me', body=message).execute()
            logger.info(f"Email sent to {to} with ID: {sent_message['id']}")
            return sent_message
        except Exception as e:
            logger.error(f"Error sending email to {to}: {e}")
            raise

    def create_draft(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        try:
            sender = "me"
            message = self.create_message(sender, to, subject, body)
            draft = {'message': message}
            created_draft = self.service.users().drafts().create(userId='me', body=draft).execute()
            logger.info(f"Draft created for {to} with ID: {created_draft['id']}")
            return created_draft
        except Exception as e:
            logger.error(f"Error creating draft for {to}: {e}")
            raise
