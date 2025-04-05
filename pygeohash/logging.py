"""Logging configuration for pygeohash.

This module provides logging configuration for the pygeohash library.
It follows best practices for library logging by:
1. Using a library-specific logger
2. Not configuring the root logger
3. Adding a NullHandler by default
4. Providing helper functions for users to configure logging
"""

import logging
from typing import Optional, Union, Any

# Create a logger specific to the library
logger = logging.getLogger("pygeohash")

# Add a NullHandler to prevent "No handlers could be found" warnings
logger.addHandler(logging.NullHandler())


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for the specified name.

    Args:
        name: The name of the logger to get. If None, returns the main pygeohash logger.
            If specified, returns a child logger of the main pygeohash logger.

    Returns:
        logging.Logger: The requested logger instance.
    """
    if name is None:
        return logger
    return logger.getChild(name)


def set_log_level(level: Union[int, str]) -> None:
    """Set the logging level for the pygeohash library.

    Args:
        level: The logging level to set. Can be either a string (e.g., 'INFO')
            or an integer (e.g., logging.INFO).
    """
    logger.setLevel(level)


def add_stream_handler(
    level: Union[int, str] = logging.INFO,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    **handler_kwargs: Any,
) -> None:
    """Add a stream handler to the pygeohash logger.

    Args:
        level: The logging level for the handler. Defaults to INFO.
        format_string: The format string for log messages.
        **handler_kwargs: Additional keyword arguments to pass to StreamHandler.
    """
    handler = logging.StreamHandler(**handler_kwargs)
    handler.setLevel(level)
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def add_file_handler(
    filename: str,
    level: Union[int, str] = logging.INFO,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    **handler_kwargs: Any,
) -> None:
    """Add a file handler to the pygeohash logger.

    Args:
        filename: The name of the file to log to.
        level: The logging level for the handler. Defaults to INFO.
        format_string: The format string for log messages.
        **handler_kwargs: Additional keyword arguments to pass to FileHandler.
    """
    handler = logging.FileHandler(filename, **handler_kwargs)
    handler.setLevel(level)
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def remove_all_handlers() -> None:
    """Remove all handlers from the pygeohash logger."""
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    logger.addHandler(logging.NullHandler())


__all__ = [
    "logger",
    "get_logger",
    "set_log_level",
    "add_stream_handler",
    "add_file_handler",
    "remove_all_handlers",
]
