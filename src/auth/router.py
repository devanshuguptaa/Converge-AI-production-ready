import os
import pickle
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_secret_file(service: str) -> str:
    """
    Resolve client secret file path for Google services.
    """
    if service == "gmail":
        default_path = "credentials/client_secret_gmail.json"
    else:
        default_path = "credentials/client_secret_calendar.json"

    combined = "credentials/client_secret_for_gmail_and_calender.json"

    if os.path.exists(default_path):
        return default_path
    elif os.path.exists(combined):
        return combined
    else:
        raise FileNotFoundError(f"Client secret for {service} not found.")


@router.get("/login")
def login(
    user_id: str = Query(..., description="User ID from Slack/Telegram/WhatsApp"),
    channel_id: str = Query(..., description="Channel ID (slack/telegram/whatsapp)"),
    service: str = Query(
        "gmail", description="Service to authenticate (gmail or calendar)"
    ),
):
    """
    Initiate Google OAuth 2.0 Web flow.
    """
    try:
        secret_file = get_client_secret_file(service)

        # Scopes based on service
        if service == "gmail":
            from src.mcp.integrations.gmail.service import SCOPES
        else:
            from src.mcp.integrations.calendar.service import SCOPES

        redirect_uri = f"{config.redirect_uri_base}/auth/callback"

        flow = Flow.from_client_secrets_file(
            secret_file, scopes=SCOPES, redirect_uri=redirect_uri
        )

        # State parameter carries request info to the callback
        state = f"{channel_id}:{user_id}:{service}"

        auth_url, _ = flow.authorization_url(
            access_type="offline", prompt="consent", state=state
        )

        return RedirectResponse(auth_url)
    except Exception as e:
        logger.error(f"Error initiating login: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to initiate login flow: {e}"
        )


@router.get("/callback")
def callback(
    state: str = Query(..., description="State parameter containing context"),
    code: str = Query(..., description="Authorization code from Google"),
):
    """
    Handle Google OAuth callback and save the credentials.
    """
    try:
        parts = state.split(":")
        if len(parts) != 3:
            raise ValueError("Invalid state parameter format")

        channel_id, user_id, service = parts
        secret_file = get_client_secret_file(service)

        if service == "gmail":
            from src.mcp.integrations.gmail.service import SCOPES

            token_file = f"credentials/token_gmail_{channel_id}_{user_id}.pickle"
        else:
            from src.mcp.integrations.calendar.service import SCOPES

            token_file = f"credentials/token_calendar_{channel_id}_{user_id}.pickle"

        redirect_uri = f"{config.redirect_uri_base}/auth/callback"

        flow = Flow.from_client_secrets_file(
            secret_file, scopes=SCOPES, redirect_uri=redirect_uri
        )

        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save pickle file
        os.makedirs("credentials", exist_ok=True)
        with open(token_file, "wb") as token:
            pickle.dump(creds, token)

        logger.info(f"Successfully saved credentials to {token_file}")

        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f4f6f9;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .card {
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
                    text-align: center;
                    max-width: 400px;
                }
                h2 {
                    color: #2ecc71;
                    margin-top: 0;
                }
                p {
                    color: #555;
                    font-size: 16px;
                    line-height: 1.5;
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>✅ Authentication Successful!</h2>
                <p>Your Google account has been connected successfully to the AI Assistant.</p>
                <p>You can now close this tab and return to Telegram/Slack/WhatsApp to retry your command.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"Error handling oauth callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to complete authentication: {e}"
        )
