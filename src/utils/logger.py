"""
Logging Utility Module

This module provides structured logging with colored console output.
Each module can get its own logger instance with module-specific naming.

Features:
- Colored console output for different log levels
- Module-specific loggers
- Configurable log levels
- Both console and file logging support
"""

import logging
import sys
from typing import Optional

from src.config import config


# Color codes for terminal output
class LogColors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log levels.
    
    Log levels are colored as follows:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Bold Red
    """
    
    FORMATS = {
        logging.DEBUG: f"{LogColors.CYAN}%(levelname)s{LogColors.RESET} - %(name)s - %(message)s",
        logging.INFO: f"{LogColors.GREEN}%(levelname)s{LogColors.RESET} - %(name)s - %(message)s",
        logging.WARNING: f"{LogColors.YELLOW}%(levelname)s{LogColors.RESET} - %(name)s - %(message)s",
        logging.ERROR: f"{LogColors.RED}%(levelname)s{LogColors.RESET} - %(name)s - %(message)s",
        logging.CRITICAL: f"{LogColors.BOLD}{LogColors.RED}%(levelname)s{LogColors.RESET} - %(name)s - %(message)s",
    }
    
    def format(self, record):
        """Format the log record with colors."""
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Set up the root logger configuration.
    
    This function configures the root logger with:
    - Console handler with colored output
    - Optionally, file handler for production
    - Configured log level from settings
    
    Args:
        log_level: Optional log level override (DEBUG, INFO, WARNING, ERROR)
    """
    # Get log level from config or use override
    level = log_level or config.log_level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)
    
    # In production, also log to file
    if config.environment == "production":
        file_handler = logging.FileHandler("assistant.log")
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    This function returns a logger with the given name.
    The logger will use the root logger configuration set by setup_logging().
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        
    Returns:
        logging.Logger: Configured logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
        INFO - mymodule - Application started
    """
    return logging.getLogger(name)


# Set up logging when module is imported
try:
    setup_logging()
except Exception:
    # If config isn't ready yet, use default settings
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


if __name__ == "__main__":
    # Test logging
    logger = get_logger(__name__)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
