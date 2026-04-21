"""OpenRouter API client for the OpenRouter CLI Chatbot.

This module provides the OpenRouterClient class for communicating with the
OpenRouter API, including request formatting, response parsing, error handling,
and retry logic.
"""

from typing import Dict, List, Union, Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config
from .exceptions import (
    APIError,
    NetworkError,
    TimeoutError as ChatbotTimeoutError,
    ResponseParseError,
)


class OpenRouterClient:
    """Client for interacting with OpenRouter API.

    This class handles all communication with the OpenRouter API, including:
    - HTTP session management with retry logic
    - Request formatting with proper authentication
    - Response parsing and validation
    - Error handling and user-friendly error messages

    The client is designed to be reusable across different interfaces
    (CLI, web, Telegram bot, REST API) and maintains no state beyond
    configuration.

    Attributes:
        config: Application configuration containing API settings
        session: Configured requests session with retry logic
    """

    def __init__(self, config: Config):
        """Initialize client with configuration.

        Args:
            config: Application configuration with API settings
        """
        self.config = config
        self.session = self._create_session()

    def send_message(
        self, messages: List[Dict[str, str]], stream: bool = False
    ) -> Union[str, Iterator[str]]:
        """Send messages to OpenRouter API and return response.

        This is the main public method for interacting with the API.
        It handles the complete request/response cycle including error
        handling and retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     Should include system prompt as first message.
            stream: Whether to stream the response (not yet implemented)

        Returns:
            Complete response string from the assistant

        Raises:
            APIError: If API returns error response (4xx/5xx)
            ChatbotTimeoutError: If request times out
            NetworkError: If network connection fails
            ResponseParseError: If response structure is invalid
        """
        # Format the request body
        request_body = self._format_request(messages)

        try:
            # Send POST request to OpenRouter API
            response = self.session.post(
                self.config.openrouter_api_url,
                json=request_body,
                timeout=self.config.request_timeout,
            )

            # Check for HTTP errors
            if response.status_code != 200:
                return self._handle_error(response)

            # Parse and return the response
            return self._parse_response(response)

        except requests.exceptions.Timeout as e:
            raise ChatbotTimeoutError(
                "Request timed out after {} seconds. "
                "The AI service might be busy. Please try again.".format(
                    self.config.request_timeout
                )
            ) from e

        except requests.exceptions.ConnectionError as e:
            raise NetworkError(
                "Unable to connect to OpenRouter. "
                "Please check your internet connection."
            ) from e

        except requests.exceptions.RequestException as e:
            raise NetworkError(
                "Network error occurred: {}".format(str(e))
            ) from e

    def _create_session(self) -> requests.Session:
        """Create configured requests session with retry logic.

        Sets up a requests session with:
        - Exponential backoff retry strategy
        - Retry on specific HTTP status codes (500, 502, 503, 504)
        - Connection pooling for performance

        Returns:
            Configured requests.Session instance
        """
        session = requests.Session()

        # Configure retry strategy
        # Retry on server errors (5xx) with exponential backoff
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,  # Wait 1s, 2s, 4s between retries
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"],  # Only retry POST requests
        )

        # Create adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)

        # Mount adapter for both http and https
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _format_request(self, messages: List[Dict[str, str]]) -> Dict:
        """Format messages into OpenRouter API request body.

        Creates the request body structure expected by the OpenRouter API,
        including authentication headers and model selection.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            Dictionary containing the complete request body with:
            - model: The AI model to use
            - messages: The conversation history

        Note:
            Authentication is handled via session headers, not in the request body.
        """
        # Set authorization header in session
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "Content-Type": "application/json",
            }
        )

        # Create request body
        request_body = {"model": self.config.openrouter_model, "messages": messages}

        return request_body

    def _parse_response(self, response: requests.Response) -> str:
        """Extract assistant message from API response.

        Parses the OpenRouter API response structure and extracts the
        assistant's message content. Validates the response structure
        and raises an error if the format is unexpected.

        Args:
            response: HTTP response from OpenRouter API

        Returns:
            The assistant's message content as a string

        Raises:
            ResponseParseError: If response structure is invalid or missing
                expected fields
        """
        try:
            data = response.json()
        except ValueError as e:
            raise ResponseParseError("Failed to parse API response as JSON") from e

        # Validate response structure
        if "choices" not in data:
            raise ResponseParseError("API response missing 'choices' field")

        if not data["choices"] or len(data["choices"]) == 0:
            raise ResponseParseError("API response 'choices' array is empty")

        choice = data["choices"][0]

        if "message" not in choice:
            raise ResponseParseError("API response choice missing 'message' field")

        message = choice["message"]

        if "content" not in message:
            raise ResponseParseError("API response message missing 'content' field")

        return message["content"]

    def _handle_error(self, response: requests.Response) -> str:
        """Convert API error responses to user-friendly messages.

        Maps HTTP status codes to appropriate exception types with
        user-friendly error messages. Does not expose sensitive information.

        Args:
            response: HTTP error response from OpenRouter API

        Raises:
            APIError: With user-friendly message and status code
        """
        status_code = response.status_code

        # Try to extract error message from response
        try:
            error_data = response.json()
            api_message = error_data.get("error", {}).get("message", "")
        except (ValueError, AttributeError):
            api_message = ""

        # Map status codes to user-friendly messages
        if status_code == 401:
            raise APIError(
                "Authentication failed. Please check your API key in the .env file.",
                status_code=401,
            )

        elif status_code == 429:
            raise APIError(
                "Rate limit exceeded. Please wait a moment before trying again.",
                status_code=429,
            )

        elif status_code == 400:
            message = "Invalid request."
            if api_message:
                message += " {}".format(api_message)
            raise APIError(message, status_code=400)

        elif status_code == 404:
            raise APIError(
                "API endpoint not found. The service might be unavailable.",
                status_code=404,
            )

        elif 500 <= status_code < 600:
            raise APIError(
                "OpenRouter service is experiencing issues. Please try again later.",
                status_code=status_code,
            )

        else:
            message = "API request failed with status {}.".format(status_code)
            if api_message:
                message += " {}".format(api_message)
            raise APIError(message, status_code=status_code)
