"""Logging configuration for the Artifact Preprocessor Agent."""

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", verbose: bool = False) -> None:
    """Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        verbose: If True, sets level to DEBUG
    """
    if verbose:
        level = "DEBUG"

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )

    # Set specific loggers to appropriate levels
    logging.getLogger("artifact_preprocessor").setLevel(numeric_level)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name, defaults to calling module

    Returns:
        Configured logger instance
    """
    if name is None:
        name = __name__
    return logging.getLogger(name)
