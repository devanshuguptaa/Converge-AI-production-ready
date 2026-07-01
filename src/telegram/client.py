import asyncio
import httpx
from src.config import config
from src.database import get_or_create_session, add_message, get_session_history
from src.agent.core import process_message
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TelegramBot:
    def __init__(self):
        self.enabled = config.telegram.enabled
        self.token = config.telegram.bot_token
        self.client = httpx.AsyncClient(timeout=30.0)
        self.offset = 0
        self.task = None

    async def initialize(self):
        """
        Initialize the Telegram Bot.
        Checks connection and starts the polling loop.
        """
        if not self.enabled:
            logger.info("Telegram integration is disabled.")
            return

        if not self.token:
            logger.error("Telegram bot token is not configured.")
            return

        try:
            logger.info("Initializing Telegram bot...")
            url = f"https://api.telegram.org/bot{self.token}/getMe"
            response = await self.client.get(url)
            if response.status_code == 200:
                bot_info = response.json().get("result", {})
                logger.info(
                    f"✅ Telegram bot authenticated successfully: @{bot_info.get('username')}"
                )
                # Start polling loop as background task
                self.task = asyncio.create_task(self.polling_loop())
            else:
                logger.error(
                    f"Failed to authenticate Telegram bot. Status: {response.status_code}, Body: {response.text}"
                )
        except Exception as e:
            logger.error(f"Error initializing Telegram bot: {e}", exc_info=True)

    async def close(self):
        """
        Stop polling and close the HTTP client.
        """
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        await self.client.aclose()
        logger.info("Telegram bot closed.")

    async def polling_loop(self):
        """
        Background task to poll for new messages using getUpdates.
        """
        logger.info("Starting Telegram long polling loop...")
        while True:
            try:
                url = f"https://api.telegram.org/bot{self.token}/getUpdates"
                params = {"offset": self.offset, "timeout": 20}
                # Timeout on the client must be slightly larger than polling timeout
                response = await self.client.get(url, params=params, timeout=25.0)

                if response.status_code == 200:
                    data = response.json()
                    updates = data.get("result", [])
                    for update in updates:
                        self.offset = update.get("update_id") + 1
                        message = update.get("message")
                        if message and "text" in message:
                            # Process messages asynchronously to avoid blocking polling
                            asyncio.create_task(self.handle_message(message))
                else:
                    logger.error(
                        f"Error fetching updates from Telegram: Status {response.status_code}, Body {response.text}"
                    )
                    await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Telegram polling loop: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def handle_message(self, message: dict):
        """
        Route message to agent and send the response back.
        """
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        user = message.get("from", {})
        username = user.get("username") or user.get("first_name") or str(chat_id)
        text = message.get("text", "")

        logger.info(
            f"Received Telegram message from '{username}' ({chat_id}): {text[:50]}..."
        )

        try:
            # 1. Create or get session (we use chat_id as user_id and "telegram" as channel_id)
            session_id = get_or_create_session(
                user_id=str(chat_id), channel_id="telegram", thread_ts=None
            )

            # 2. Persist user message in DB
            add_message(session_id, "user", text)

            # 3. Retrieve conversation history
            history = get_session_history(session_id)

            # 4. Process with agent
            logger.info(f"Routing Telegram message to agent (Session: {session_id})")
            response = await process_message(
                user_message=text,
                session_id=session_id,
                user_id=str(chat_id),
                channel_id="telegram",
                history=history,
            )

            if not response or not response.strip():
                response = "I processed your request, but I couldn't formulate a response. How else can I help?"

            # 5. Send reply
            success = await self.send_message(chat_id, response)
            if success:
                # 6. Save assistant message in DB
                add_message(session_id, "assistant", response)
                logger.info(f"Response sent to Telegram chat {chat_id}")
            else:
                logger.error(f"Failed to send response to Telegram chat {chat_id}")

        except Exception as e:
            logger.error(f"Error processing Telegram message: {e}", exc_info=True)
            try:
                await self.send_message(
                    chat_id,
                    "⚠️ Sorry, I encountered an internal error processing your message. Please try again.",
                )
            except Exception:
                pass

    async def send_message(self, chat_id: int, text: str) -> bool:
        """
        Send a plain text message back to a Telegram chat.
        """
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        try:
            response = await self.client.post(url, json=payload)
            if response.status_code == 200:
                return True
            else:
                logger.error(
                    f"Failed to send Telegram message. Status: {response.status_code}, Body: {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False


# Global instance of the Telegram bot
telegram_bot = TelegramBot()
