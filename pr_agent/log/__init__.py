import os
import json
import logging
import sys
from enum import Enum

from loguru import logger

ANALYTICS_FOLDER = os.getenv("ANALYTICS_FOLDER", "")
os.environ["AUTO_CAST_FOR_DYNACONF"] = "false"


class LoggingFormat(str, Enum):
    """
    Enumeration of supported logging formats.

    Attributes:
        CONSOLE: Human-readable format for console output.
        JSON: Machine-readable JSON format for log processing.
    """

    CONSOLE = "CONSOLE"
    JSON = "JSON"


def json_format(record: dict) -> str:
    """
    Format a log record as a JSON string.

    Args:
        record: The loguru Record object to format.

    Returns:
        str: The formatted message string.
    """
    return record["message"]


def analytics_filter(record: dict) -> bool:
    """
    Filter to only include analytics logs.

    Args:
        record: The loguru Record object to filter.

    Returns:
        bool: True if the record is an analytics record, False otherwise.
    """
    return record.get("analytics", False)


def inv_analytics_filter(record: dict) -> bool:
    """
    Filter to exclude analytics logs.

    Args:
        record: The loguru Record object to filter.

    Returns:
        bool: True if the record is NOT an analytics record, False otherwise.
    """
    return not record.get("analytics", False)


def setup_logger(level: str = "INFO", fmt: LoggingFormat = LoggingFormat.CONSOLE):
    """
    Configure and set up the logging system.

    This function configures loguru loggers with the specified log level and format.
    It sets up stdout logging for normal logs and file logging for analytics if
    ANALYTICS_FOLDER is specified.

    Args:
        level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Default is "INFO".
        fmt: The logging format to use (CONSOLE or JSON). Default is CONSOLE.

    Returns:
        Logger: The configured logger instance.
    """
    log_level = logging.getLevelName(level.upper())
    if type(log_level) is not int:
        log_level = logging.INFO

    if (
        fmt == LoggingFormat.JSON and os.getenv("LOG_SANE", "0").lower() == "0"
    ):  # better debugging github_app
        logger.remove(None)
        logger.add(
            sys.stdout,
            filter=inv_analytics_filter,
            level=log_level,
            format="{message}",
            colorize=False,
            serialize=True,
        )
    elif fmt == LoggingFormat.CONSOLE:  # does not print the 'extra' fields
        logger.remove(None)
        logger.add(
            sys.stdout, level=log_level, colorize=True, filter=inv_analytics_filter
        )

    log_folder = ANALYTICS_FOLDER
    if log_folder:
        pid = os.getpid()
        log_file = os.path.join(log_folder, f"pr-agent.{pid}.log")
        logger.add(
            log_file,
            filter=analytics_filter,
            level=log_level,
            format="{message}",
            colorize=False,
            serialize=True,
        )

    return logger


def get_logger(*args, **kwargs):
    """
    Get the configured logger instance.

    This is a convenience function that returns the global logger instance.
    Any args or kwargs are ignored for compatibility with other logging systems.

    Returns:
        Logger: The configured logger instance.
    """
    return logger
