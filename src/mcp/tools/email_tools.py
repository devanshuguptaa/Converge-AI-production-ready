from typing import Dict, Any, List
from ..integrations.gmail.reader import GmailReader
from ..integrations.gmail.sender import GmailSender
from ..integrations.gmail.service import GmailService
from ..core.permissions import PermissionManager, MCPScope

class EmailTools:
    def __init__(self, permission_manager: PermissionManager, client_secret_path: str, token_path: str = 'token_gmail.pickle'):
        self.permission_manager = permission_manager
        self.service = GmailService(client_secret_path, token_path=token_path)
        self.reader = GmailReader(self.service)
        self.sender = GmailSender(self.service)

    def get_tools(self) -> Dict[str, Any]:
        return {
            "list_recent_emails": self.list_recent_emails_tool(),
            "get_email_details": self.get_email_details_tool(),
            "get_multiple_email_details": self.get_multiple_email_details_tool(),
            "send_email": self.send_email_tool(),
            "create_draft": self.create_draft_tool(),
            "summarize_email_thread": self.summarize_email_thread_tool()
        }

    def list_recent_emails_tool(self):
        def run(limit: int = 5, query: str = ""):
            self.permission_manager.validate_tool_access("list_recent_emails", MCPScope.GMAIL_READ)
            # Get message IDs first
            messages = self.reader.list_messages(query=query, max_results=limit)
            if not messages:
                return []
            # Fetch details for each message to provide meaningful content
            message_ids = [msg['id'] for msg in messages]
            return self.reader.get_messages_batch(message_ids)
        
        return {
            "name": "list_recent_emails",
            "description": "Lists recent emails from the inbox with full details including subject, sender, date, and snippet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of emails to list"},
                    "query": {"type": "string", "description": "Optional Gmail search query"}
                },
                "required": ["limit"]
            },
            "run": run
        }

    def get_email_details_tool(self):
        def run(message_id: str):
            self.permission_manager.validate_tool_access("get_email_details", MCPScope.GMAIL_READ)
            return self.reader.get_message_details(message_id)

        return {
            "name": "get_email_details",
            "description": "Gets the full details of a specific email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "The ID of the email message"}
                },
                "required": ["message_id"]
            },
            "run": run
        }

    def get_multiple_email_details_tool(self):
        def run(message_ids: List[str]):
            self.permission_manager.validate_tool_access("get_email_details", MCPScope.GMAIL_READ)
            return self.reader.get_messages_batch(message_ids)

        return {
            "name": "get_multiple_email_details",
            "description": "Gets details for multiple emails at once. Efficient for summaries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_ids": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of email IDs to fetch"
                    }
                },
                "required": ["message_ids"]
            },
            "run": run
        }

    def send_email_tool(self):
        def run(to: str, subject: str, body: str):
            self.permission_manager.validate_tool_access("send_email", MCPScope.GMAIL_SEND)
            return self.sender.send_email(to, subject, body)

        return {
            "name": "send_email",
            "description": "Sends an email to a recipient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"}
                },
                "required": ["to", "subject", "body"]
            },
            "run": run
        }

    def create_draft_tool(self):
        def run(to: str, subject: str, body: str):
            self.permission_manager.validate_tool_access("create_draft", MCPScope.GMAIL_SEND) # Using SEND scope for drafts too
            return self.sender.create_draft(to, subject, body)

        return {
            "name": "create_draft",
            "description": "Creates a draft email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"}
                },
                "required": ["to", "subject", "body"]
            },
            "run": run
        }

    def summarize_email_thread_tool(self):
        def run(thread_id: str):
            self.permission_manager.validate_tool_access("summarize_email_thread", MCPScope.GMAIL_READ)
            # Fetch thread details
            thread_data = self.reader.get_thread(thread_id)
            if not thread_data:
                return "Thread not found or error fetching thread."
            
            # In a real MCP, we might process this further. 
            # For now, we return the structured data so the Client (LLM) can summarize it.
            return thread_data

        return {
            "name": "summarize_email_thread",
            "description": "Fetches an email thread to be summarized. Returns structured messages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string", "description": "The ID of the email thread"}
                },
                "required": ["thread_id"]
            },
            "run": run
        }
