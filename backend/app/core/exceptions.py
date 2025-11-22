"""
Custom exception classes for consistent error handling.
"""

from enum import Enum
from typing import Any

from fastapi import status


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""

    # Resource errors
    RECIPE_NOT_FOUND = "RECIPE_NOT_FOUND"
    COLLECTION_NOT_FOUND = "COLLECTION_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    HOUSEHOLD_NOT_FOUND = "HOUSEHOLD_NOT_FOUND"
    MEAL_PLAN_NOT_FOUND = "MEAL_PLAN_NOT_FOUND"
    SHOPPING_LIST_NOT_FOUND = "SHOPPING_LIST_NOT_FOUND"

    # Authentication & Authorization
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Validation errors
    INVALID_INPUT = "INVALID_INPUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # External services
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppException(Exception):
    """Base exception class for application errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class RecipeNotFoundError(AppException):
    """Raised when a recipe cannot be found."""

    def __init__(self, recipe_id: int | None = None, details: dict[str, Any] | None = None):
        message = f"Recipe {recipe_id} not found" if recipe_id else "Recipe not found"
        super().__init__(
            message=message,
            error_code=ErrorCode.RECIPE_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class CollectionNotFoundError(AppException):
    """Raised when a collection cannot be found."""

    def __init__(
        self, collection_id: int | None = None, details: dict[str, Any] | None = None
    ):
        message = (
            f"Collection {collection_id} not found" if collection_id else "Collection not found"
        )
        super().__init__(
            message=message,
            error_code=ErrorCode.COLLECTION_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class UnauthorizedAccessError(AppException):
    """Raised when a user attempts an unauthorized action."""

    def __init__(self, message: str = "Unauthorized access", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class InvalidCredentialsError(AppException):
    """Raised when authentication credentials are invalid."""

    def __init__(
        self, message: str = "Invalid credentials", details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_CREDENTIALS,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class InvalidInputError(AppException):
    """Raised when input validation fails."""

    def __init__(
        self, message: str = "Invalid input", details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_INPUT,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class RateLimitExceededError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self, message: str = "Rate limit exceeded", details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


class ExternalServiceError(AppException):
    """Raised when an external service fails."""

    def __init__(
        self, service: str, message: str | None = None, details: dict[str, Any] | None = None
    ):
        message = message or f"{service} service error"
        super().__init__(
            message=message,
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details or {"service": service},
        )


class AIServiceError(AppException):
    """Raised when AI service fails."""

    def __init__(self, message: str = "AI service error", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.AI_SERVICE_ERROR,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )
