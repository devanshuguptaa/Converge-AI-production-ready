"""
Logging Utility Module

This module provides structured logging for the entire application.
It creates module-specific loggers with consistent formatting.

Features:
- Colored console output for development
- JSON formatting for production
- Module-specific loggers
- Configurable log levels
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import config


# ANSI color codes for console output
class LogColors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Log level colors
    DEBUG = "\033[36m"      # Cyan
    INFO = "\033[32m"       # Green
    WARNING = "\033[33m"    # Yellow
    ERROR = "\033[31m"      # Red
    CRITICAL = "\033[35m"   # Magenta


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log levels in console output.
    
    This makes logs easier to read during development.
    """
    
    FORMATS = {
        logging.DEBUG: f"{LogColors.DEBUG}%(levelname)s{LogColors.RESET} - %(name)s - %(message)s",
        logging.INFO: f"{LogColors.INFO}%(levelname)s{LogColors.RESET} - %(name)s - %(message)s",
        logging.WARNING: f"{LogColors.WARNING}%(levelname)s{LogColors.RESET} - %(name)s - %(message)s",
        logging.ERROR: f"{LogColors.ERROR}%(levelname)s{LogColors.RESET} - %(name)s - %(message)s",
        logging.CRITICAL: f"{LogColors.CRITICAL}%(levelname)s{LogColors.RESET} - %(name)s - %(message)s",
    }
    
    def format(self, record):
        """Format the log record with appropriate color."""
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging() -> None:
    """
    Set up the root logger with appropriate handlers and formatters.
    
    This function should be called once at application startup.
    It configures:
    - Console handler with colored output (development)
    - File handler with detailed logs (optional)
    - Log level from configuration
    """
    # Get log level from config
    log_level = getattr(logging, config.log_level.upper())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if config.environment == "development":
        # Use colored formatter for development
        console_handler.setFormatter(ColoredFormatter())
    else:
        # Use simple formatter for production
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    
    # Optionally add file handler for production
    if config.environment == "production":
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    This creates a child logger under the root logger, allowing
    for module-specific logging that inherits the root configuration.
    
    Args:
        name: Name of the module (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
        >>> logger.error("An error occurred", exc_info=True)
    """
    return logging.getLogger(name)


# Initialize logging when module is imported
setup_logging()


if __name__ == "__main__":
    # Test logging
    logger = get_logger("test")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test exception logging
    try:
        1 / 0
    except Exception:
        logger.error("An exception occurred", exc_info=True)
