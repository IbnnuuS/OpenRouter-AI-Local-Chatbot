"""Configuration management for the OpenRouter CLI Chatbot.

This module provides centralized configuration management with support for
environment variables and sensible defaults.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .exceptions import ConfigurationError


@dataclass
class Config:
    """Application configuration loaded from environment and defaults.

    This dataclass holds all configuration values for the chatbot application,
    including API settings, file paths, and timeout values. Configuration can
    be loaded from environment variables with fallback to default values.

    Attributes:
        openrouter_api_key: API key for OpenRouter authentication (required)
        openrouter_api_url: OpenRouter API endpoint URL
        openrouter_model: Model identifier to use for chat completions
        memory_file_path: Path to conversation history JSON file
        system_prompt_file_path: Path to system prompt text file
        request_timeout: Timeout in seconds for API requests
        max_retries: Maximum number of retry attempts for failed requests
        default_system_prompt: Fallback system prompt if file is missing
    """

    # API Configuration
    openrouter_api_key: str
    openrouter_api_url: str = "https://openrouter.ai/api/v1/chat/completions"
    openrouter_model: str = "stepfun/step-3.5-flash"

    # File Paths
    memory_file_path: str = "memory.json"
    system_prompt_file_path: str = "system_prompt.txt"

    # API Settings
    request_timeout: int = 30
    max_retries: int = 3

    # Default System Prompt
    default_system_prompt: str = "You are a helpful AI assistant."

    @classmethod
    def load_from_env(cls) -> "Config":
        """Load configuration from environment variables and .env file.

        This method loads configuration values from environment variables,
        falling back to default values for optional settings. The .env file
        is automatically loaded using python-dotenv.

        Returns:
            Config instance with values from environment or defaults

        Raises:
            ConfigurationError: If required configuration (API key) is missing
        """
        # Load .env file if it exists
        load_dotenv()

        # Read required API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "OPENROUTER_API_KEY is required. "
                "Please set it in your .env file."
            )

        # Read optional configuration with defaults
        api_url = os.getenv(
            "OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions"
        )
        model = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
        memory_file = os.getenv("MEMORY_FILE_PATH", "memory.json")
        system_prompt_file = os.getenv("SYSTEM_PROMPT_FILE_PATH", "system_prompt.txt")

        # Read numeric settings with defaults
        timeout_str = os.getenv("REQUEST_TIMEOUT", "30")
        max_retries_str = os.getenv("MAX_RETRIES", "3")

        try:
            timeout = int(timeout_str)
        except ValueError:
            timeout = 30

        try:
            max_retries = int(max_retries_str)
        except ValueError:
            max_retries = 3

        # Create and return Config instance
        return cls(
            openrouter_api_key=api_key,
            openrouter_api_url=api_url,
            openrouter_model=model,
            memory_file_path=memory_file,
            system_prompt_file_path=system_prompt_file,
            request_timeout=timeout,
            max_retries=max_retries,
        )

    def validate(self) -> None:
        """Validate required configuration values are present.

        Checks that all required configuration values (particularly the API key)
        are present and valid. This method should be called after loading
        configuration to ensure the application can start successfully.

        Raises:
            ConfigurationError: If validation fails (e.g., missing API key)
        """
        if not self.openrouter_api_key or not self.openrouter_api_key.strip():
            raise ConfigurationError(
                "API key is missing or empty. "
                "Please set OPENROUTER_API_KEY in your .env file."
            )
