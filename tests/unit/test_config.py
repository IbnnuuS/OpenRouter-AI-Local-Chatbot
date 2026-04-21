"""Unit tests for configuration management module.

Tests the Config class and its methods for loading configuration from
environment variables and validating settings.
"""

import os
import pytest
from unittest.mock import patch

from src.config import Config
from src.exceptions import ConfigurationError


class TestConfigLoadFromEnv:
    """Tests for Config.load_from_env() classmethod."""

    def test_load_with_api_key_only(self):
        """Test loading config with only required API key set."""
        with patch.dict(
            os.environ, {"OPENROUTER_API_KEY": "test_api_key_123"}, clear=True
        ):
            config = Config.load_from_env()

            assert config.openrouter_api_key == "test_api_key_123"
            assert (
                config.openrouter_api_url
                == "https://openrouter.ai/api/v1/chat/completions"
            )
            assert config.openrouter_model == "mistralai/mistral-7b-instruct:free"
            assert config.memory_file_path == "memory.json"
            assert config.system_prompt_file_path == "system_prompt.txt"
            assert config.request_timeout == 30
            assert config.max_retries == 3

    def test_load_with_all_overrides(self):
        """Test loading config with all environment variables overridden."""
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "custom_key",
                "OPENROUTER_API_URL": "https://custom.api.url/v1/chat",
                "OPENROUTER_MODEL": "custom/model:free",
                "MEMORY_FILE_PATH": "custom_memory.json",
                "SYSTEM_PROMPT_FILE_PATH": "custom_prompt.txt",
                "REQUEST_TIMEOUT": "60",
                "MAX_RETRIES": "5",
            },
            clear=True,
        ):
            config = Config.load_from_env()

            assert config.openrouter_api_key == "custom_key"
            assert config.openrouter_api_url == "https://custom.api.url/v1/chat"
            assert config.openrouter_model == "custom/model:free"
            assert config.memory_file_path == "custom_memory.json"
            assert config.system_prompt_file_path == "custom_prompt.txt"
            assert config.request_timeout == 60
            assert config.max_retries == 5

    def test_load_missing_api_key_raises_error(self):
        """Test that missing API key raises ConfigurationError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                Config.load_from_env()

            assert "OPENROUTER_API_KEY is required" in str(exc_info.value)

    def test_load_with_partial_overrides(self):
        """Test loading config with some environment variables overridden."""
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "test_key",
                "OPENROUTER_MODEL": "openchat/openchat-7b:free",
                "REQUEST_TIMEOUT": "45",
            },
            clear=True,
        ):
            config = Config.load_from_env()

            assert config.openrouter_api_key == "test_key"
            assert config.openrouter_model == "openchat/openchat-7b:free"
            assert config.request_timeout == 45
            # Defaults for non-overridden values
            assert (
                config.openrouter_api_url
                == "https://openrouter.ai/api/v1/chat/completions"
            )
            assert config.memory_file_path == "memory.json"
            assert config.max_retries == 3

    def test_load_with_invalid_timeout_uses_default(self):
        """Test that invalid timeout value falls back to default."""
        with patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": "test_key", "REQUEST_TIMEOUT": "not_a_number"},
            clear=True,
        ):
            config = Config.load_from_env()

            assert config.request_timeout == 30  # Default value

    def test_load_with_invalid_max_retries_uses_default(self):
        """Test that invalid max_retries value falls back to default."""
        with patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": "test_key", "MAX_RETRIES": "invalid"},
            clear=True,
        ):
            config = Config.load_from_env()

            assert config.max_retries == 3  # Default value

    def test_load_with_empty_api_key_raises_error(self):
        """Test that empty API key raises ConfigurationError."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                Config.load_from_env()

            assert "OPENROUTER_API_KEY is required" in str(exc_info.value)

    def test_load_with_zero_timeout(self):
        """Test loading config with zero timeout value."""
        with patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": "test_key", "REQUEST_TIMEOUT": "0"},
            clear=True,
        ):
            config = Config.load_from_env()

            assert config.request_timeout == 0

    def test_load_with_negative_timeout_uses_value(self):
        """Test that negative timeout value is accepted (validation happens later)."""
        with patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": "test_key", "REQUEST_TIMEOUT": "-10"},
            clear=True,
        ):
            config = Config.load_from_env()

            # Load accepts the value; validation should catch this
            assert config.request_timeout == -10

    def test_load_preserves_whitespace_in_api_key(self):
        """Test that API key with whitespace is preserved as-is."""
        with patch.dict(
            os.environ, {"OPENROUTER_API_KEY": "  key_with_spaces  "}, clear=True
        ):
            config = Config.load_from_env()

            # Whitespace is preserved; validation may handle this
            assert config.openrouter_api_key == "  key_with_spaces  "


class TestConfigValidate:
    """Tests for Config.validate() method."""

    def test_validate_with_valid_api_key(self):
        """Test that validate passes with a valid API key."""
        config = Config(openrouter_api_key="valid_api_key_123")
        # Should not raise any exception
        config.validate()

    def test_validate_with_empty_api_key_raises_error(self):
        """Test that validate raises ConfigurationError for empty API key."""
        config = Config(openrouter_api_key="")

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "API key is missing or empty" in str(exc_info.value)

    def test_validate_with_whitespace_only_api_key_raises_error(self):
        """Test that validate raises ConfigurationError for whitespace-only API key."""
        config = Config(openrouter_api_key="   ")

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "API key is missing or empty" in str(exc_info.value)

    def test_validate_with_api_key_containing_whitespace(self):
        """Test that validate passes with API key that has leading/trailing whitespace."""
        config = Config(openrouter_api_key="  valid_key  ")
        # Should not raise - the key has content beyond whitespace
        config.validate()
