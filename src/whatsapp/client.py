"""
WhatsApp Client Module using Evolution API

This module handles communication with the WhatsApp Evolution API gateway,
including instance creation, webhook setup, QR code generation, and sending messages.
"""

import os
from pathlib import Path
import httpx
from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Ensure data directory exists for storing QR code files
DATA_DIR = Path(config.database_path).parent
DATA_DIR.mkdir(parents=True, exist_ok=True)
QR_HTML_PATH = DATA_DIR / "whatsapp_qr.html"


class WhatsAppClient:
    """
    Client for interacting with the Evolution API WhatsApp gateway.
    """

    def __init__(self):
        self.enabled = config.whatsapp.enabled
        self.api_url = config.whatsapp.api_url.rstrip("/")
        self.api_key = config.whatsapp.api_key
        self.instance_name = config.whatsapp.instance_name
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def headers(self) -> dict[str, str]:
        """Get standard authorization headers for the gateway."""
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    async def close(self):
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def initialize(self, webhook_url: str | None = None):
        """
        Initialize the WhatsApp instance.
        Checks if it exists, creates it if not, sets the webhook, and handles connection.
        """
        if not self.enabled:
            logger.info("WhatsApp integration is disabled.")
            return

        try:
            logger.info(f"Initializing WhatsApp integration with gateway: {self.api_url}")
            
            # 1. Check if the instance exists
            exists = await self.check_instance_exists()
            if not exists:
                logger.info(f"Instance '{self.instance_name}' does not exist. Creating...")
                await self.create_instance()
            else:
                logger.info(f"Instance '{self.instance_name}' already exists.")

            # 2. Set the webhook if a URL is provided
            if webhook_url:
                logger.info(f"Setting WhatsApp webhook to: {webhook_url}")
                await self.set_webhook(webhook_url)

            # 3. Check connection status and QR code
            await self.check_connection_and_qr()

        except Exception as e:
            logger.error(f"Error initializing WhatsApp client: {e}", exc_info=True)

    async def check_instance_exists(self) -> bool:
        """Fetch all instances and check if our target instance exists."""
        url = f"{self.api_url}/instance/fetchInstances"
        try:
            response = await self.client.get(url, headers=self.headers)
            if response.status_code == 200:
                instances = response.json()
                # Evolution API returns instances as a list of dicts
                if isinstance(instances, list):
                    for inst in instances:
                        if inst.get("name") == self.instance_name or inst.get("instanceName") == self.instance_name:
                            return True
            return False
        except Exception as e:
            logger.error(f"Failed to fetch instances from Evolution API: {e}")
            raise

    async def create_instance(self):
        """Create a new WhatsApp instance on the gateway."""
        url = f"{self.api_url}/instance/create"
        payload = {
            "instanceName": self.instance_name,
            "token": self.api_key,
            "number": "",
            "options": {
                "reject_call": True,
                "msg_call": "Voice/Video calls are not supported by the AI assistant.",
                "groups_ignore": False,
                "always_online": True,
                "read_messages": True,
                "read_status": True
            }
        }
        try:
            response = await self.client.post(url, headers=self.headers, json=payload)
            if response.status_code not in (200, 201):
                logger.error(f"Failed to create instance. Status: {response.status_code}, Body: {response.text}")
                response.raise_for_status()
            logger.info(f"Successfully created WhatsApp instance: {self.instance_name}")
        except Exception as e:
            logger.error(f"Error creating WhatsApp instance: {e}")
            raise

    async def set_webhook(self, webhook_url: str):
        """Configure the webhook URL for the WhatsApp instance events."""
        url = f"{self.api_url}/webhook/set/{self.instance_name}"
        payload = {
            "webhook": {
                "enabled": True,
                "url": webhook_url,
                "byEvents": True,
                "events": [
                    "MESSAGES_UPSERT",
                    "SEND_MESSAGE"
                ]
            }
        }
        # Note: Evolution API expects boolean values in lowercase JSON. Python's True maps to true.
        try:
            response = await self.client.post(url, headers=self.headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Failed to set webhook. Status: {response.status_code}, Body: {response.text}")
                response.raise_for_status()
            logger.info("WhatsApp webhook set successfully.")
        except Exception as e:
            logger.error(f"Error configuring WhatsApp webhook: {e}")
            raise

    async def check_connection_and_qr(self):
        """Check if WhatsApp is connected. If not, generate and save the QR code page."""
        url = f"{self.api_url}/instance/connect/{self.instance_name}"
        try:
            response = await self.client.get(url, headers=self.headers)
            data = response.json()

            # Check if already connected
            status = data.get("status") or data.get("instance", {}).get("status")
            if status == "connected" or data.get("state") == "open":
                logger.info("WhatsApp bot is CONNECTED and ready to receive messages!")
                if QR_HTML_PATH.exists():
                    try:
                        QR_HTML_PATH.unlink()
                        logger.info("Removed stale QR code file.")
                    except Exception as e:
                        logger.warning(f"Could not remove stale QR file: {e}")
                return

            # Check if QR code is returned
            qr_base64 = data.get("base64")
            if not qr_base64:
                qr_base64 = data.get("qrcode", {}).get("base64")

            if qr_base64:
                logger.warning(
                    f"⚠️ WhatsApp bot is NOT connected. QR code generated.\n"
                    f"👉 Please open this file in your browser to scan: {QR_HTML_PATH.absolute()}"
                )
                self._write_qr_html(qr_base64)
            else:
                logger.warning(f"WhatsApp connection state: {status}. QR code not yet available. Response: {data}")

        except Exception as e:
            logger.error(f"Error checking connection status: {e}")

    def _write_qr_html(self, base64_image: str):
        """Write an HTML page containing the QR code to facilitate user scanning."""
        # Ensure correct data URL schema
        if not base64_image.startswith("data:"):
            base64_image = f"data:image/png;base64,{base64_image}"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp Bot Authentication</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }}
        .card {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 400px;
        }}
        h2 {{
            color: #075e54;
            margin-top: 0;
        }}
        p {{
            color: #4a4a4a;
            font-size: 14px;
            line-height: 1.5;
        }}
        img {{
            border: 1px solid #ddd;
            border-radius: 8px;
            margin: 20px 0;
            max-width: 100%;
        }}
        .footer {{
            font-size: 11px;
            color: #888;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h2>Scan WhatsApp QR Code</h2>
        <p>Open WhatsApp on your phone, go to Linked Devices, and scan this QR code to authenticate the AI Assistant.</p>
        <img src="{base64_image}" alt="WhatsApp QR Code" />
        <p><strong>Note:</strong> This page will automatically update once authenticated and the file will be deleted.</p>
        <div class="footer">Powered by Converge AI</div>
    </div>
</body>
</html>
"""
        try:
            QR_HTML_PATH.write_text(html_content, encoding="utf-8")
            logger.info(f"QR code HTML successfully written to {QR_HTML_PATH}")
        except Exception as e:
            logger.error(f"Failed to write QR HTML file: {e}")

    async def send_message(self, number: str, text: str) -> bool:
        """
        Send a plain text message to a WhatsApp number.
        The number can be a single number (e.g. '1234567890') or JID formatted.
        """
        if not self.enabled:
            logger.warning("WhatsApp sending is disabled (WHATSAPP_ENABLED is False).")
            return False

        # Ensure the number is formatted correctly (strip leading +, spaces, etc.)
        clean_number = "".join(filter(str.isdigit, number))
        if not clean_number:
            logger.error(f"Invalid WhatsApp number format: '{number}'")
            return False

        url = f"{self.api_url}/message/sendText/{self.instance_name}"
        payload = {
            "number": clean_number,
            "options": {
                "delay": 1000,
                "presence": "composing",
                "linkPreview": True
            },
            "textMessage": {
                "text": text
            }
        }

        try:
            response = await self.client.post(url, headers=self.headers, json=payload)
            if response.status_code in (200, 201):
                logger.info(f"WhatsApp message sent to {clean_number}")
                return True
            else:
                logger.error(f"Failed to send WhatsApp message. Status: {response.status_code}, Body: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False


# Global instance of the WhatsApp client
whatsapp_client = WhatsAppClient()
