"""
Application-wide constants.

This module defines all magic numbers and configuration values used throughout
the application to improve maintainability and make configuration easier.
"""

# AI Service Constants
MAX_RECIPES_IN_PROMPT = 50  # Maximum recipes to include in AI prompt to avoid token overflow
AI_REQUEST_TIMEOUT_SECONDS = 60.0  # Timeout for AI API requests
AI_TEMPERATURE = 0.7  # Temperature for AI model responses (0.0-1.0, higher = more creative)

# Security Constants
MIN_SECRET_KEY_LENGTH = 32  # Minimum length for SECRET_KEY in characters
REFRESH_TOKEN_LENGTH = 64  # Length of refresh token in bytes

# Password Requirements
MIN_PASSWORD_LENGTH = 8  # Minimum password length for user accounts

# Rate Limiting (defined in settings, documented here for reference)
# RATE_LIMIT_PER_MINUTE: 60 requests per minute
# RATE_LIMIT_PER_HOUR: 1000 requests per hour
# AI_RATE_LIMIT_PER_HOUR: 50 AI requests per hour

# Authentication Rate Limits
AUTH_RATE_LIMIT_REGISTRATION = "5/hour"  # Rate limit for registration endpoint
AUTH_RATE_LIMIT_TEST_MODE = "10000/hour"  # Effectively unlimited for tests

# Token Expiration (defined in settings, documented here for reference)
# ACCESS_TOKEN_EXPIRE_MINUTES: 15 minutes (short-lived for security)
# REFRESH_TOKEN_EXPIRE_DAYS: 30 days (long-lived for UX)

# File Upload Constraints (defined in settings, documented here for reference)
# MAX_UPLOAD_SIZE_MB: 10 MB maximum upload size

# Pagination
DEFAULT_PAGE_SIZE = 20  # Default number of items per page
MAX_PAGE_SIZE = 100  # Maximum items per page

# PDF Export Constants
PDF_MARGIN = 15  # Page margin in mm
PDF_AUTO_PAGE_BREAK_MARGIN = 15  # Bottom margin for automatic page breaks
PDF_FOOTER_Y_POSITION = -15  # Y position for footer (from bottom)
PDF_LINE_WIDTH_THIN = 0.5  # Thin line width for borders
PDF_LINE_WIDTH_NORMAL = 1  # Normal line width
PDF_BOX_WIDTH = 180  # Standard box width in mm
PDF_COLUMN_WIDTH = 90  # Width for two-column layout
PDF_LINE_HEIGHT = 6  # Standard line height
PDF_PADDING = 5  # Standard padding
PDF_LABEL_WIDTH = 30  # Width for labels in metadata boxes
PDF_INDENT = 5  # Indentation for lists
PDF_COVER_VERTICAL_POSITION = 80  # Y position for cover title
PDF_TOC_MIN_RECIPES = 1  # Minimum recipes to show table of contents (>1 means 2+)
PDF_MIN_CHAR_CODE = 32  # Minimum character code for text cleaning

# HTTP Status Codes (most commonly used)
HTTP_RATE_LIMIT_ERROR = 429  # Rate limit exceeded
HTTP_UNAUTHORIZED = 401  # Unauthorized access
