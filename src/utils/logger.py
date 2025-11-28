"""
Logging Module
==============
Centralized logging configuration for Hiero Review Tool.
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Default log directory
DEFAULT_LOG_DIR = Path.home() / ".hiero_review" / "logs"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Get level from environment or use default
        if level is None:
            env_level = os.environ.get("HIERO_REVIEW_LOG_LEVEL", "INFO")
            level = getattr(logging, env_level.upper(), logging.INFO)
        
        logger.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(console_handler)
        
        # File handler (if log directory exists or can be created)
        try:
            log_dir = Path(os.environ.get("HIERO_REVIEW_LOG_DIR", DEFAULT_LOG_DIR))
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"hiero_review_{datetime.now():%Y%m%d}.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            logger.addHandler(file_handler)
        except (OSError, PermissionError):
            # Can't create log file, continue with console only
            pass
    
    return logger


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Setup root logging configuration.
    
    Args:
        level: Log level
        log_file: Optional log file path
    """
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
        except (OSError, PermissionError):
            pass
    
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=handlers
    )


class LogContext:
    """Context manager for logging operations with timing."""
    
    def __init__(self, logger: logging.Logger, operation: str, level: int = logging.INFO):
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.log(self.level, f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is not None:
            self.logger.error(
                f"Failed: {self.operation} after {elapsed:.2f}s - {exc_type.__name__}: {exc_val}"
            )
        else:
            self.logger.log(self.level, f"Completed: {self.operation} in {elapsed:.2f}s")
        
        return False  # Don't suppress exceptions


# Convenience function for timed operations
def log_operation(logger: logging.Logger, operation: str, level: int = logging.INFO):
    """Create a LogContext for timing an operation."""
    return LogContext(logger, operation, level)


# Module-level logger for this module
_logger = get_logger(__name__)


def log_error(message: str, exc: Optional[Exception] = None) -> None:
    """Log an error message with optional exception."""
    if exc:
        _logger.error(f"{message}: {type(exc).__name__}: {exc}")
    else:
        _logger.error(message)


def log_warning(message: str) -> None:
    """Log a warning message."""
    _logger.warning(message)


def log_info(message: str) -> None:
    """Log an info message."""
    _logger.info(message)


def log_debug(message: str) -> None:
    """Log a debug message."""
    _logger.debug(message)

