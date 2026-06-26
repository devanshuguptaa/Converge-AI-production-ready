"""
WhatsApp Webhook Router

This module defines the FastAPI router that receives incoming events (messages)
from the Evolution API WhatsApp gateway and routes them to the AI agent.
"""

from fastapi import APIRouter, Request, Header, HTTPException, status
from fastapi.responses import HTMLResponse
from src.config import config
from src.utils.logger import get_logger
from src.database import get_or_create_session, add_message, get_session_history
from src.whatsapp.client import whatsapp_client

logger = get_logger(__name__)

router = APIRouter(
    prefix="/webhooks/whatsapp",
    tags=["whatsapp"]
)


def extract_message_text(message_data: dict) -> str | None:
    """
    Extract the text content from different WhatsApp message types.
    """
    message = message_data.get("message")
    if not message:
        return None

    # 1. Standard conversation text
    if "conversation" in message:
        return message["conversation"]

    # 2. Extended text message (contains links, styling)
    if "extendedTextMessage" in message:
        return message.get("extendedTextMessage", {}).get("text")

    # 3. Image/Video caption (fallback if they send a photo with a caption)
    if "imageMessage" in message:
        return message.get("imageMessage", {}).get("caption")
    if "videoMessage" in message:
        return message.get("videoMessage", {}).get("caption")

    return None


@router.post("")
async def receive_whatsapp_event(request: Request, apikey: str | None = Header(None)):
    """
    FastAPI endpoint for Evolution API webhooks.
    """
    # 1. Security Check (Optional but highly recommended for Production)
    expected_secret = config.whatsapp.webhook_secret
    if expected_secret:
        # Check if the header or query parameter matches the expected webhook secret
        if apikey != expected_secret:
            logger.warning("Unauthorized webhook request received.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook token"
            )

    try:
        payload = await request.json()
    except Exception:
        logger.error("Failed to parse JSON body of WhatsApp webhook.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    event_type = payload.get("event")
    logger.debug(f"Received WhatsApp webhook event: {event_type}")

    # We only process message upsert events (incoming messages)
    if event_type not in ("messages.upsert", "MESSAGES_UPSERT"):
        return {"status": "ignored", "reason": "non-upsert event"}

    data = payload.get("data")
    if not data:
        return {"status": "ignored", "reason": "empty data object"}

    key = data.get("key", {})
    from_me = key.get("fromMe", False)

    # 2. Prevent loops: Ignore messages sent by the bot itself
    if from_me:
        return {"status": "ignored", "reason": "message from self"}

    remote_jid = key.get("remoteJid")
    if not remote_jid:
        return {"status": "error", "reason": "missing remoteJid"}

    # Extract text content
    text = extract_message_text(data)
    if not text or not text.strip():
        return {"status": "ignored", "reason": "empty or unsupported message type"}

    # Extract user pushname or use JID username
    push_name = data.get("pushName") or remote_jid.split("@")[0]

    logger.info(f"Received WhatsApp message from '{push_name}' ({remote_jid}): {text[:50]}...")

    # Process async to avoid blocking the webhook response (fast response is required by APIs)
    import asyncio
    asyncio.create_task(
        process_whatsapp_message(
            remote_jid=remote_jid,
            user_name=push_name,
            text=text
        )
    )

    return {"status": "received"}


async def process_whatsapp_message(remote_jid: str, user_name: str, text: str):
    """
    Runs the agent execution, saves context to database, and sends reply.
    """
    try:
        # 1. Create or get database session for WhatsApp channel
        # We represent user_id as remote_jid, and channel_id as "whatsapp"
        session_id = get_or_create_session(
            user_id=remote_jid,
            channel_id="whatsapp",
            thread_ts=None
        )

        # 2. Persist user message in DB
        add_message(session_id, "user", text)

        # 3. Retrieve conversation history from DB
        history = get_session_history(session_id)

        # 4. Call AI Agent
        logger.info(f"Routing WhatsApp message to AI agent (Session: {session_id})")
        
        from src.agent.core import process_message
        response = await process_message(
            user_message=text,
            session_id=session_id,
            user_id=remote_jid,
            channel_id="whatsapp",
            history=history
        )

        # 5. Fallback check for empty response
        if not response or not response.strip():
            response = "I processed your request, but I couldn't formulate a response. How else can I help?"

        # 6. Send message back via WhatsApp Web client
        success = await whatsapp_client.send_message(number=remote_jid, text=response)
        
        if success:
            # 7. Persist assistant response in DB
            add_message(session_id, "assistant", response)
            logger.info(f"WhatsApp response successfully sent & saved to session {session_id}")
        else:
            logger.error(f"Failed to send response to WhatsApp number {remote_jid}")

    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}", exc_info=True)
        # Notify the user on WhatsApp of the internal failure
        try:
            await whatsapp_client.send_message(
                number=remote_jid,
                text="⚠️ Sorry, I encountered an internal error processing your message. Please try again."
            )
        except Exception:
            pass


@router.get("/qr", response_class=HTMLResponse)
async def get_qr_page():
    """
    Serve the WhatsApp authentication QR code page.
    """
    if not config.whatsapp.enabled:
        return "<h3>WhatsApp integration is disabled in configuration.</h3>"
    
    # Check if the QR file exists, otherwise trigger a check
    from src.whatsapp.client import QR_HTML_PATH
    if not QR_HTML_PATH.exists():
        await whatsapp_client.check_connection_and_qr()
        
    if QR_HTML_PATH.exists():
        return QR_HTML_PATH.read_text(encoding="utf-8")
        
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhatsApp Connected</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f0f2f5;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 400px;
            }
            h2 {
                color: #075e54;
                margin-top: 0;
            }
            p {
                color: #4a4a4a;
                font-size: 14px;
                line-height: 1.5;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>WhatsApp Connected!</h2>
            <p>Your WhatsApp bot is already connected and running.</p>
        </div>
    </body>
    </html>
    """
