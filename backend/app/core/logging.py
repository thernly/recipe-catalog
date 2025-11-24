"""
Structured logging configuration using structlog.

This module configures structured logging for the application with:
- JSON formatting in production for machine parsing
- Pretty console output in development for human readability
- Correlation ID support for tracing requests across services
"""

import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """
    Configure structlog with appropriate processors and formatting.

    Uses JSON formatting in production and console formatting in development.
    """
    # Determine if we're in production
    is_production = settings.ENVIRONMENT == "production"

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Build processor chain
    processors = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add caller info (file, line, function)
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ],
        ),
        # Add correlation_id from context if present
        structlog.contextvars.merge_contextvars,
    ]

    # Add appropriate final processor based on environment
    if is_production:
        # JSON output for production (machine-readable)
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Pretty console output for development (human-readable)
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__ of the calling module)

    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)
