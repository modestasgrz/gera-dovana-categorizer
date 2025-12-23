"""Custom exception classes"""


class APIKeyError(Exception):
    """Raised when API key is invalid or missing."""


class APINetworkError(Exception):
    """Raised when network errors occur during API calls."""


class APIRateLimitError(Exception):
    """Raised when API rate limits are exceeded."""
