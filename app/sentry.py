"""Sentry configuration and initialization"""

import logging
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.config import settings

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """Initialize Sentry SDK for error tracking and performance monitoring"""
    if not settings.sentry_dsn:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return

    try:
        # Configure Sentry SDK
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.sentry_environment,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            profiles_sample_rate=settings.sentry_profiles_sample_rate,
            # Enable FastAPI integration
            integrations=[
                FastApiIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR,  # Send errors as events
                ),
            ],
            # Set release version (can be overridden by environment)
            release=f"tdg-mvp@{settings.sentry_environment}",
            # Add custom tags
            default_tags={
                "service": "tdg-mvp",
                "component": "backend",
            },
            # Configure before_send to filter out certain errors
            before_send=before_send_filter,
        )
        logger.info(
            f"Sentry initialized successfully for environment: {settings.sentry_environment}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_filter(event, hint):
    """Filter out certain events before sending to Sentry"""
    # Don't send events for certain error types
    if "exception" in hint:
        exc_type = type(hint["exception"]).__name__
        # Filter out common expected errors
        if exc_type in ["ValidationError", "HTTPException"]:
            return None

    return event


def capture_exception(exception: Exception, context: Optional[dict] = None) -> None:
    """Capture an exception with optional context"""
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_tag(key, value)
            sentry_sdk.capture_exception(exception)
    else:
        sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info", context: Optional[dict] = None) -> None:
    """Capture a message with optional context"""
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_tag(key, value)
            sentry_sdk.capture_message(message, level=level)
    else:
        sentry_sdk.capture_message(message, level=level)


def set_user_context(
    user_id: str, email: Optional[str] = None, username: Optional[str] = None
) -> None:
    """Set user context for Sentry events"""
    sentry_sdk.set_user(
        {
            "id": user_id,
            "email": email,
            "username": username,
        }
    )


def set_tag(key: str, value: str) -> None:
    """Set a tag for Sentry events"""
    sentry_sdk.set_tag(key, value)


def set_context(key: str, data: dict) -> None:
    """Set context data for Sentry events"""
    sentry_sdk.set_context(key, data)
