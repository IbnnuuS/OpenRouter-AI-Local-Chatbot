"""Custom exception classes for the OpenRouter CLI Chatbot.

This module defines the exception hierarchy used throughout the application
for consistent error handling and reporting.
"""


class ChatbotError(Exception):
    """Base exception for all chatbot-related errors.

    All custom exceptions in the chatbot application inherit from this base class,
    allowing for broad exception handling when needed while maintaining specific
    error types for detailed error handling.
    """

    pass


class ConfigurationError(ChatbotError):
    """Configuration-related errors.

    Raised when there are issues with application configuration, such as:
    - Missing required environment variables (e.g., API key)
    - Invalid configuration values
    - Inaccessible configuration files

    These errors are typically fatal and prevent application startup.
    """

    pass


class APIError(ChatbotError):
    """OpenRouter API errors.

    Raised when the OpenRouter API returns an error response, such as:
    - Authentication failures (401)
    - Rate limiting (429)
    - Server errors (5xx)
    - Invalid requests (4xx)

    Attributes:
        status_code (int, optional): HTTP status code from the API response
    """

    def __init__(self, message: str, status_code: int = None):
        """Initialize APIError with message and optional status code.

        Args:
            message: Descriptive error message
            status_code: HTTP status code from the API response (optional)
        """
        self.status_code = status_code
        super().__init__(message)


class NetworkError(ChatbotError):
    """Network connectivity errors.

    Raised when there are network-level issues preventing communication
    with the OpenRouter API, such as:
    - Connection failures
    - DNS resolution errors
    - Network unreachable conditions

    These errors are typically recoverable with retry logic.
    """

    pass


class TimeoutError(ChatbotError):
    """Request timeout errors.

    Raised when an API request exceeds the configured timeout period.
    This may indicate:
    - Slow network conditions
    - API service overload
    - Unusually long response generation

    These errors are typically recoverable with retry logic.
    """

    pass


class MemoryError(ChatbotError):
    """Memory persistence errors.

    Raised when there are issues with conversation history persistence, such as:
    - File I/O errors when reading or writing memory.json
    - Corrupted conversation history data
    - Insufficient disk space

    These errors are typically recoverable, with the application continuing
    to use in-memory conversation history.
    """

    pass


class ResponseParseError(ChatbotError):
    """API response parsing errors.

    Raised when the OpenRouter API returns a response that cannot be parsed
    or has an unexpected structure, such as:
    - Missing expected fields in the response
    - Invalid JSON structure
    - Unexpected data types

    These errors may indicate API changes or malformed responses.
    """

    pass
