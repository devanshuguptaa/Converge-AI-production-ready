from typing import List, Dict, Any
from .service import GmailService
import base64
import logging

logger = logging.getLogger(__name__)

class GmailReader:
    def __init__(self, gmail_service: GmailService):
        self.service = gmail_service.get_service()

    def list_messages(self, query: str = '', max_results: int = 10) -> List[Dict[str, Any]]:
        try:
            results = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            return messages
        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            return []

    def get_messages_batch(self, message_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetches details for multiple messages.
        Currently implements a sequential fetch to ensure stability and avoid SSL race conditions.
        """
        results = []
        for msg_id in message_ids:
            try:
                # Reuse existing logic
                details = self.get_message_details(msg_id)
                if details:
                    results.append(details)
            except Exception as e:
                logger.error(f"Error fetching message {msg_id} in batch: {e}")
        return results

    def get_message_details(self, message_id: str) -> Dict[str, Any]:
        try:
            message = self.service.users().messages().get(userId='me', id=message_id).execute()
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            body = self._get_body(payload)
            
            return {
                'id': message_id,
                'threadId': message.get('threadId'),
                'subject': subject,
                'sender': sender,
                'date': date,
                'snippet': message.get('snippet'),
                'body': body
            }
        except Exception as e:
            logger.error(f"Error getting message details for {message_id}: {e}")
            return {}

    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        try:
            thread = self.service.users().threads().get(userId='me', id=thread_id).execute()
            messages = thread.get('messages', [])
            
            parsed_messages = []
            for msg in messages:
                payload = msg.get('payload', {})
                headers = payload.get('headers', [])
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                body = self._get_body(payload)
                parsed_messages.append({
                    'sender': sender,
                    'date': date,
                    'body': body[:500] + "..." if len(body) > 500 else body # Truncate for context window
                })
            
            return {
                'threadId': thread_id,
                'messageCount': len(messages),
                'messages': parsed_messages
            }
        except Exception as e:
            logger.error(f"Error getting thread {thread_id}: {e}")
            return {}

    def _get_body(self, payload):
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode()
        elif 'body' in payload:
            data = payload['body'].get('data')
            if data:
                body += base64.urlsafe_b64decode(data).decode()
        return body
