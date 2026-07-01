"""
Slack AI Assistant - Main Application

This is the entry point for the FastAPI application that powers the Slack AI assistant.

The application integrates:
- FastAPI for web framework and webhooks
- Slack Bolt for Slack event handling
- Google Gemini for LLM and embeddings
- LangChain v1 for agent orchestration
- ChromaDB for RAG (vector storage)
- mem0 for long-term memory
- MCP for GitHub/Notion integration
- APScheduler for task scheduling

Architecture:
    FastAPI App
        ↓
    Slack Webhook → Slack Bolt Handler
        ↓
    AI Agent (LangChain v1)
        ↓
    Tools: RAG + Memory + MCP + Slack Actions
"""

import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from src.config import config, validate_config
from src.database import initialize_database
from src.utils.logger import get_logger
from src.whatsapp.webhook import router as whatsapp_router
from src.auth.router import router as auth_router

logger = get_logger(__name__)


# Global references to services
# These will be initialized in the lifespan context manager
slack_app = None
agent = None
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    This context manager handles startup and shutdown logic:
    - Startup: Initialize all services (database, RAG, memory, MCP, Slack)
    - Shutdown: Gracefully stop all services

    Args:
        app: FastAPI application instance
    """
    logger.info("=" * 60)
    logger.info("Starting Slack AI Assistant")
    logger.info("=" * 60)

    # Validate configuration
    is_valid, errors = validate_config()
    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        raise RuntimeError("Invalid configuration. Please check your .env file.")

    logger.info("✅ Configuration validated")

    # Initialize database
    logger.info("Initializing database...")
    initialize_database()
    logger.info("✅ Database initialized")

    # Initialize RAG system (if enabled)
    if config.rag.enabled:
        logger.info("Initializing RAG system...")
        try:
            from src.rag.vectorstore import initialize_vectorstore

            await initialize_vectorstore()
            logger.info("✅ RAG system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}", exc_info=True)
            logger.warning("Continuing without RAG")

    # Initialize Memory system (if enabled)
    if config.memory.enabled:
        logger.info("Initializing memory system...")
        try:
            from src.memory.mem0_client import initialize_memory

            initialize_memory()
            logger.info("✅ Memory system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize memory: {e}", exc_info=True)
            logger.warning("Continuing without memory")

    # Initialize MCP (if enabled)
    if config.mcp.enabled:
        logger.info("Initializing MCP servers...")
        try:
            from src.mcp.registry import initialize_mcp

            await initialize_mcp()
            logger.info("✅ MCP servers initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MCP: {e}", exc_info=True)
            logger.warning("Continuing without MCP")

    # Initialize AI Agent
    logger.info("Initializing AI agent...")
    try:
        from src.agent.core import initialize_agent

        global agent
        agent = await initialize_agent()
        logger.info("✅ AI agent initialized")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}", exc_info=True)
        raise RuntimeError("Cannot start without AI agent")

    # Initialize Task Scheduler
    logger.info("Initializing task scheduler...")
    try:
        from src.scheduler.tasks import initialize_scheduler

        global scheduler
        scheduler = initialize_scheduler()
        logger.info("✅ Task scheduler initialized")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)
        logger.warning("Continuing without scheduler")

    # Initialize Slack App
    logger.info("Initializing Slack app...")
    try:
        from src.slack.app import initialize_slack_app

        global slack_app
        slack_app = await initialize_slack_app()
        logger.info("✅ Slack app initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Slack app: {e}", exc_info=True)
        raise RuntimeError("Cannot start without Slack app")

    # Initialize WhatsApp Client
    if config.whatsapp.enabled:
        logger.info("Initializing WhatsApp client...")
        try:
            from src.whatsapp.client import whatsapp_client

            await whatsapp_client.initialize(webhook_url=config.whatsapp.webhook_url)
            logger.info("✅ WhatsApp client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp client: {e}", exc_info=True)
            logger.warning("Continuing without WhatsApp")

    # Initialize Telegram Bot
    if config.telegram.enabled:
        logger.info("Initializing Telegram bot...")
        try:
            from src.telegram.client import telegram_bot

            await telegram_bot.initialize()
            logger.info("✅ Telegram bot initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}", exc_info=True)
            logger.warning("Continuing without Telegram")

    # Start background indexer (if RAG enabled)
    if config.rag.enabled:
        logger.info("Starting background message indexer...")
        try:
            from src.rag.indexer import start_indexer, set_slack_client
            from src.slack.tools import set_slack_client as set_tools_slack_client
            from src.scheduler.tasks import (
                set_slack_client as set_scheduler_slack_client,
            )

            # Get Slack client from the app
            slack_client = slack_app.client

            # Pass Slack client to all modules that need it
            set_slack_client(slack_client)
            set_tools_slack_client(slack_client)
            set_scheduler_slack_client(slack_client)

            start_indexer()
            logger.info("✅ Background indexer started")
        except Exception as e:
            logger.error(f"Failed to start indexer: {e}", exc_info=True)
            logger.warning("Continuing without background indexing")

    logger.info("=" * 60)
    logger.info("🚀 Slack AI Assistant is ready!")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Log Level: {config.log_level}")
    logger.info(f"RAG Enabled: {config.rag.enabled}")
    logger.info(f"Memory Enabled: {config.memory.enabled}")
    logger.info(f"MCP Enabled: {config.mcp.enabled}")
    logger.info(f"Telegram Enabled: {config.telegram.enabled}")
    logger.info("=" * 60)

    # Application is now running
    yield

    # Shutdown sequence
    logger.info("=" * 60)
    logger.info("Shutting down Slack AI Assistant...")
    logger.info("=" * 60)

    # Stop scheduler
    if scheduler:
        logger.info("Stopping task scheduler...")
        try:
            scheduler.shutdown()
            logger.info("✅ Task scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    # Stop MCP servers
    if config.mcp.enabled:
        logger.info("Stopping MCP servers...")
        try:
            from src.mcp.registry import shutdown_mcp

            await shutdown_mcp()
            logger.info("✅ MCP servers stopped")
        except Exception as e:
            logger.error(f"Error stopping MCP: {e}")

    # Close WhatsApp client session
    if config.whatsapp.enabled:
        logger.info("Closing WhatsApp client...")
        try:
            from src.whatsapp.client import whatsapp_client

            await whatsapp_client.close()
            logger.info("✅ WhatsApp client closed")
        except Exception as e:
            logger.error(f"Error closing WhatsApp client: {e}")

    # Close Telegram bot session
    if config.telegram.enabled:
        logger.info("Closing Telegram bot...")
        try:
            from src.telegram.client import telegram_bot

            await telegram_bot.close()
            logger.info("✅ Telegram bot closed")
        except Exception as e:
            logger.error(f"Error closing Telegram bot: {e}")

    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Slack AI Assistant",
    description="AI-powered Slack assistant with RAG, Memory, and MCP integration",
    version="0.1.0",
    lifespan=lifespan,
)

# Include WhatsApp webhook router
app.include_router(whatsapp_router)

# Include Google Authentication router
app.include_router(auth_router)


@app.get("/")
async def root():
    """
    Root endpoint - health check.

    Returns:
        dict: Status information
    """
    return {
        "status": "ok",
        "service": "Slack AI Assistant",
        "version": "0.1.0",
        "features": {
            "rag": config.rag.enabled,
            "memory": config.memory.enabled,
            "mcp": config.mcp.enabled,
        },
    }


@app.get("/health")
async def health():
    """
    Health check endpoint.

    Returns:
        dict: Health status of all services
    """
    health_status = {
        "status": "healthy",
        "services": {
            "database": "ok",
            "slack": "ok" if slack_app else "not_initialized",
            "agent": "ok" if agent else "not_initialized",
            "rag": "ok" if config.rag.enabled else "disabled",
            "memory": "ok" if config.memory.enabled else "disabled",
            "mcp": "ok" if config.mcp.enabled else "disabled",
            "scheduler": "ok" if scheduler else "not_initialized",
        },
    }

    return health_status


@app.post("/slack/events")
async def slack_events(request: Request):
    """
    Slack events webhook endpoint.

    This endpoint receives all Slack events (messages, mentions, etc.)
    and forwards them to the Slack Bolt handler.

    Args:
        request: FastAPI request object containing Slack event payload

    Returns:
        Response: Slack expects a 200 OK response
    """
    if not slack_app:
        logger.error("Slack app not initialized")
        return JSONResponse(
            status_code=503, content={"error": "Slack app not initialized"}
        )

    # Get request body
    body = await request.body()
    headers = dict(request.headers)

    # Forward to Slack Bolt handler
    try:
        from src.slack.app import handle_slack_event

        response = await handle_slack_event(body, headers)
        return Response(
            content=response.get("body", ""),
            status_code=response.get("status", 200),
            headers=response.get("headers", {}),
        )
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


# Signal handlers for graceful shutdown
def handle_shutdown_signal(signum, frame):
    """
    Handle shutdown signals (SIGINT, SIGTERM).

    This ensures graceful shutdown when the application is stopped.
    """
    logger.info(f"Received signal {signum}, initiating shutdown...")
    # FastAPI will handle the shutdown via the lifespan context manager


# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.port,
        reload=config.environment == "development",
        log_level=config.log_level.lower(),
    )
