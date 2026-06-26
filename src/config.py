"""
Configuration Management Module

This module handles all application configuration using Pydantic Settings.
It loads environment variables from .env file and validates them.

Features:
- Type-safe configuration with Pydantic
- Automatic .env file loading
- Validation of required fields
- Default values for optional settings
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

# Get the project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent


class SlackConfig(BaseSettings):
    """
    Slack-specific configuration settings.
    
    Attributes:
        bot_token: Slack bot user OAuth token (starts with xoxb-)
        app_token: Slack app-level token for Socket Mode (starts with xapp-)
        signing_secret: Slack signing secret for request verification
    """
    bot_token: str = Field(..., alias="SLACK_BOT_TOKEN")
    app_token: str = Field(..., alias="SLACK_APP_TOKEN")
    signing_secret: str = Field(..., alias="SLACK_SIGNING_SECRET")
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class GeminiConfig(BaseSettings):
    """
    Google Gemini API configuration.
    
    Attributes:
        api_key: Google Gemini API key
        chat_model: Model name for chat completions (default: gemini-2.0-flash-exp)
        embedding_model: Model name for embeddings (default: text-embedding-004)
    """
    api_key: str = Field(..., alias="GEMINI_API_KEY")
    chat_model: str = Field(default="gemini-2.0-flash-exp", alias="GEMINI_CHAT_MODEL")
    embedding_model: str = Field(
        default="models/text-embedding-004",
        alias="GEMINI_EMBEDDING_MODEL"
    )
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class MemoryConfig(BaseSettings):
    """
    mem0 long-term memory configuration.
    
    Attributes:
        api_key: mem0 API key
        enabled: Whether memory features are enabled
    """
    api_key: str = Field(..., alias="MEM0_API_KEY")
    enabled: bool = Field(default=True, alias="MEMORY_ENABLED")
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class RAGConfig(BaseSettings):
    """
    RAG (Retrieval Augmented Generation) configuration.
    
    Attributes:
        enabled: Whether RAG is enabled
        max_results: Maximum number of results to retrieve
        indexer_interval_minutes: How often to index new messages (in minutes)
        vector_db_path: Path to ChromaDB storage directory
    """
    enabled: bool = Field(default=True, alias="RAG_ENABLED")
    max_results: int = Field(default=10, alias="RAG_MAX_RESULTS")
    indexer_interval_minutes: int = Field(
        default=60,
        alias="RAG_INDEXER_INTERVAL_MINUTES"
    )
    vector_db_path: str = Field(default="./data/chromadb", alias="VECTOR_DB_PATH")
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class MCPConfig(BaseSettings):
    """
    MCP (Model Context Protocol) configuration for GitHub and Notion.
    
    Attributes:
        enabled: Whether MCP integration is enabled
        github_token: GitHub Personal Access Token
        notion_token: Notion Integration Token
    """
    enabled: bool = Field(default=True, alias="MCP_ENABLED")
    github_token: str | None = Field(default=None, alias="GITHUB_PERSONAL_ACCESS_TOKEN")
    notion_token: str | None = Field(default=None, alias="NOTION_API_TOKEN")
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class WhatsAppConfig(BaseSettings):
    """
    WhatsApp configuration settings via Evolution API.
    
    Attributes:
        enabled: Whether WhatsApp integration is enabled
        api_url: Base URL for the WhatsApp Evolution API gateway
        api_key: Secret key used to authenticate with Evolution API
        webhook_secret: Optional secret for validating incoming WhatsApp webhooks
        instance_name: Evolution API instance name
    """
    enabled: bool = Field(default=False, alias="WHATSAPP_ENABLED")
    api_url: str = Field(default="http://whatsapp-gateway:8080", alias="WHATSAPP_API_URL")
    api_key: str = Field(default="your-whatsapp-api-key-here", alias="WHATSAPP_API_KEY")
    webhook_secret: str | None = Field(default=None, alias="WHATSAPP_WEBHOOK_SECRET")
    webhook_url: str | None = Field(default=None, alias="WHATSAPP_WEBHOOK_URL")
    instance_name: str = Field(default="converge_assistant", alias="WHATSAPP_INSTANCE_NAME")
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class AppConfig(BaseSettings):
    """
    Main application configuration.
    
    This is the root configuration class that combines all sub-configurations.
    
    Attributes:
        slack: Slack configuration
        gemini: Gemini API configuration
        memory: mem0 memory configuration
        rag: RAG configuration
        mcp: MCP configuration
        whatsapp: WhatsApp configuration
        database_path: Path to SQLite database file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        environment: Application environment (development, production)
        host: FastAPI server host
        port: FastAPI server port
        dm_policy: DM policy (open, pairing, allowlist)
        allowed_users: List of allowed user IDs (for allowlist policy)
    """
    
    # Sub-configurations
    slack: SlackConfig = Field(default_factory=SlackConfig)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    whatsapp: WhatsAppConfig = Field(default_factory=WhatsAppConfig)
    
    # Database
    database_path: str = Field(default="./data/assistant.db", alias="DATABASE_PATH")
    
    # Application settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        alias="LOG_LEVEL"
    )
    environment: Literal["development", "production"] = Field(
        default="development",
        alias="ENVIRONMENT"
    )
    
    # FastAPI settings
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # DM Policy
    dm_policy: Literal["open", "pairing", "allowlist"] = Field(
        default="open",
        alias="DM_POLICY"
    )
    allowed_users: list[str] = Field(default_factory=list, alias="ALLOWED_USERS")
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables
    )


# Global configuration instance
# This will be imported by other modules
config = AppConfig()


# Validation function to check if configuration is complete
def validate_config() -> tuple[bool, list[str]]:
    """
    Validate that all required configuration is present.
    
    Returns:
        tuple: (is_valid, list_of_errors)
            - is_valid: True if configuration is valid
            - list_of_errors: List of error messages (empty if valid)
    """
    errors = []
    
    # Check Slack configuration
    if not config.slack.bot_token or config.slack.bot_token == "xoxb-your-bot-token-here":
        errors.append("SLACK_BOT_TOKEN is not configured")
    
    if not config.slack.app_token or config.slack.app_token == "xapp-your-app-token-here":
        errors.append("SLACK_APP_TOKEN is not configured")
    
    # Check Gemini configuration
    if not config.gemini.api_key or config.gemini.api_key == "your-gemini-api-key-here":
        errors.append("GEMINI_API_KEY is not configured")
    
    # Check mem0 configuration (if enabled)
    if config.memory.enabled:
        if not config.memory.api_key or config.memory.api_key == "your-mem0-api-key-here":
            errors.append("MEM0_API_KEY is not configured (or disable memory with MEMORY_ENABLED=false)")
    
    # Check MCP configuration (if enabled)
    if config.mcp.enabled:
        if not config.mcp.github_token:
            errors.append("GITHUB_PERSONAL_ACCESS_TOKEN is not configured (or disable MCP with MCP_ENABLED=false)")
            
    # Check WhatsApp configuration (if enabled)
    if config.whatsapp.enabled:
        if not config.whatsapp.api_key or config.whatsapp.api_key == "your-whatsapp-api-key-here":
            errors.append("WHATSAPP_API_KEY is not configured (or disable WhatsApp with WHATSAPP_ENABLED=false)")
        if not config.whatsapp.api_url:
            errors.append("WHATSAPP_API_URL is not configured")
    
    return (len(errors) == 0, errors)


if __name__ == "__main__":
    # Test configuration loading
    print("Configuration loaded successfully!")
    print(f"Environment: {config.environment}")
    print(f"Log Level: {config.log_level}")
    print(f"Gemini Model: {config.gemini.chat_model}")
    print(f"RAG Enabled: {config.rag.enabled}")
    print(f"Memory Enabled: {config.memory.enabled}")
    print(f"MCP Enabled: {config.mcp.enabled}")
    
    # Validate configuration
    is_valid, errors = validate_config()
    if is_valid:
        print("\n✅ Configuration is valid!")
    else:
        print("\n❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
