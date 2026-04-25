"""
Logging configuration for OrangeHRM automation framework.

Sets up centralized logging with file and console handlers.
"""

import logging
import os
from config import LoggingConfig, Paths

# Ensure log directory exists
Paths.ensure_directories()


def setup_logging():
    """
    Configure logging for the entire framework.
    
    Creates:
    - Console handler: INFO level for interactive output
    - File handler: DEBUG level for detailed logs
    """
    logger = logging.getLogger("automation")
    logger.setLevel(LoggingConfig.LOG_LEVEL)
    
    # Prevent duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Console handler - INFO level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
        datefmt=LoggingConfig.LOG_DATE_FORMAT
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler - DEBUG level
    file_handler = logging.FileHandler(LoggingConfig.LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        LoggingConfig.LOG_FORMAT,
        datefmt=LoggingConfig.LOG_DATE_FORMAT
    )
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name (str): Logger name, typically __name__
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(f"automation.{name}")


# Initialize logger at module load
logger = setup_logging()
