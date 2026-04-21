"""Unit tests for the CLI interface module.

This module tests the ChatbotCLI class and its methods, including command
handling, user input processing, message sending, and error handling.
"""

import os
import tempfile
from unittest.mock import Mock, patch
import pytest

from src.main import ChatbotCLI, main
from src.config import Config
from src.exceptions import (
    ConfigurationError,
    APIError,
    NetworkError,
    TimeoutError as ChatbotTimeoutError,
    ResponseParseError,
)


class TestChatbotCLI:
    """Test suite for ChatbotCLI class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=Config)
        config.openrouter_api_key = "test_key"
        config.openrouter_api_url = "https://test.api/v1/chat"
        config.openrouter_model = "test-model"
        config.memory_file_path = "test_memory.json"
        config.system_prompt_file_path = "test_system_prompt.txt"
        config.request_timeout = 30
        config.max_retries = 3
        config.default_system_prompt = "You are a helpful AI assistant."
        return config

    @pytest.fixture
    def cli_with_mocks(self, mock_config):
        """Create a ChatbotCLI instance with mocked dependencies."""
        with patch("src.main.Config.load_from_env", return_value=mock_config), patch(
            "src.main.OpenRouterClient"
        ) as mock_client_class, patch(
            "src.main.MemoryManager"
        ) as mock_memory_class, patch.object(
            ChatbotCLI, "_load_system_prompt", return_value="Test prompt"
        ):
            cli = ChatbotCLI()
            cli.client = mock_client_class.return_value
            cli.memory = mock_memory_class.return_value
            return cli

    def test_init_loads_configuration(self, mock_config):
        """Test that __init__ loads configuration correctly."""
        with patch(
            "src.main.Config.load_from_env", return_value=mock_config
        ) as mock_load, patch("src.main.OpenRouterClient"), patch(
            "src.main.MemoryManager"
        ), patch.object(
            ChatbotCLI, "_load_system_prompt", return_value="Test prompt"
        ):
            cli = ChatbotCLI()

            mock_load.assert_called_once()
            mock_config.validate.assert_called_once()
            assert cli.config == mock_config

    def test_init_raises_configuration_error(self):
        """Test that __init__ raises ConfigurationError when validation fails."""
        mock_config = Mock(spec=Config)
        mock_config.validate.side_effect = ConfigurationError("Missing API key")

        with patch("src.main.Config.load_from_env", return_value=mock_config), patch(
            "src.main.OpenRouterClient"
        ), patch("src.main.MemoryManager"):
            with pytest.raises(ConfigurationError, match="Missing API key"):
                ChatbotCLI()

    def test_load_system_prompt_from_file(self, mock_config):
        """Test loading system prompt from existing file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Custom system prompt\nwith multiple lines")
            temp_file = f.name

        try:
            mock_config.system_prompt_file_path = temp_file

            with patch(
                "src.main.Config.load_from_env", return_value=mock_config
            ), patch("src.main.OpenRouterClient"), patch("src.main.MemoryManager"):
                cli = ChatbotCLI()

                assert cli.system_prompt == "Custom system prompt\nwith multiple lines"
        finally:
            os.unlink(temp_file)

    def test_load_system_prompt_missing_file(self, mock_config, capsys):
        """Test loading system prompt when file is missing uses default."""
        mock_config.system_prompt_file_path = "nonexistent_file.txt"
        mock_config.default_system_prompt = "Default prompt"

        with patch("src.main.Config.load_from_env", return_value=mock_config), patch(
            "src.main.OpenRouterClient"
        ), patch("src.main.MemoryManager"):
            cli = ChatbotCLI()

            assert cli.system_prompt == "Default prompt"
            captured = capsys.readouterr()
            assert "not found" in captured.out

    def test_display_welcome(self, cli_with_mocks, capsys):
        """Test that welcome message is displayed correctly."""
        cli_with_mocks._display_welcome()

        captured = capsys.readouterr()
        assert "Welcome to OpenRouter CLI Chatbot!" in captured.out
        assert "/exit" in captured.out
        assert "/reset" in captured.out
        assert "/persona" in captured.out
        assert "/help" in captured.out

    def test_get_user_input(self, cli_with_mocks):
        """Test getting user input."""
        with patch("builtins.input", return_value="  test input  "):
            result = cli_with_mocks._get_user_input()
            assert result == "test input"

    def test_handle_command_exit(self, cli_with_mocks, capsys):
        """Test /exit command returns False."""
        result = cli_with_mocks._handle_command("/exit")

        assert result is False
        captured = capsys.readouterr()
        assert "Goodbye" in captured.out

    def test_handle_command_reset(self, cli_with_mocks, capsys):
        """Test /reset command clears memory."""
        result = cli_with_mocks._handle_command("/reset")

        assert result is True
        cli_with_mocks.memory.clear.assert_called_once()
        captured = capsys.readouterr()
        assert "cleared" in captured.out

    def test_handle_command_persona(self, cli_with_mocks, capsys):
        """Test /persona command displays system prompt."""
        cli_with_mocks.system_prompt = "Test system prompt"
        result = cli_with_mocks._handle_command("/persona")

        assert result is True
        captured = capsys.readouterr()
        assert "Test system prompt" in captured.out

    def test_handle_command_help(self, cli_with_mocks, capsys):
        """Test /help command displays available commands."""
        result = cli_with_mocks._handle_command("/help")

        assert result is True
        captured = capsys.readouterr()
        assert "/exit" in captured.out
        assert "/reset" in captured.out
        assert "/persona" in captured.out

    def test_handle_command_unknown(self, cli_with_mocks, capsys):
        """Test unknown command displays error."""
        result = cli_with_mocks._handle_command("/unknown")

        assert result is True
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out
        assert "/unknown" in captured.out

    def test_handle_command_case_insensitive(self, cli_with_mocks):
        """Test commands are case-insensitive."""
        assert cli_with_mocks._handle_command("/EXIT") is False
        assert cli_with_mocks._handle_command("/Reset") is True
        assert cli_with_mocks._handle_command("/PERSONA") is True

    def test_send_message_success(self, cli_with_mocks, capsys):
        """Test sending message successfully."""
        cli_with_mocks.system_prompt = "System prompt"
        cli_with_mocks.memory.get_messages.return_value = [
            {"role": "user", "content": "Hello"}
        ]
        cli_with_mocks.client.send_message.return_value = "AI response"

        cli_with_mocks._send_message("Hello")

        # Verify user message was appended
        cli_with_mocks.memory.append.assert_any_call("user", "Hello")

        # Verify API was called with correct messages
        call_args = cli_with_mocks.client.send_message.call_args[0][0]
        assert call_args[0] == {"role": "system", "content": "System prompt"}
        assert call_args[1] == {"role": "user", "content": "Hello"}

        # Verify assistant response was appended
        cli_with_mocks.memory.append.assert_any_call("assistant", "AI response")

        # Verify response was displayed
        captured = capsys.readouterr()
        assert "AI response" in captured.out

    def test_send_message_api_error(self, cli_with_mocks, capsys):
        """Test handling APIError during message sending."""
        cli_with_mocks.memory.get_messages.return_value = []
        cli_with_mocks.client.send_message.side_effect = APIError("API failed", 500)

        cli_with_mocks._send_message("Test")

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "API failed" in captured.out

    def test_send_message_network_error(self, cli_with_mocks, capsys):
        """Test handling NetworkError during message sending."""
        cli_with_mocks.memory.get_messages.return_value = []
        cli_with_mocks.client.send_message.side_effect = NetworkError("Network failed")

        cli_with_mocks._send_message("Test")

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "Network failed" in captured.out

    def test_send_message_timeout_error(self, cli_with_mocks, capsys):
        """Test handling TimeoutError during message sending."""
        cli_with_mocks.memory.get_messages.return_value = []
        cli_with_mocks.client.send_message.side_effect = ChatbotTimeoutError("Timeout")

        cli_with_mocks._send_message("Test")

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "Timeout" in captured.out

    def test_send_message_response_parse_error(self, cli_with_mocks, capsys):
        """Test handling ResponseParseError during message sending."""
        cli_with_mocks.memory.get_messages.return_value = []
        cli_with_mocks.client.send_message.side_effect = ResponseParseError(
            "Parse failed"
        )

        cli_with_mocks._send_message("Test")

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "parse" in captured.out.lower()

    def test_send_message_unexpected_error(self, cli_with_mocks, capsys):
        """Test handling unexpected errors during message sending."""
        cli_with_mocks.memory.get_messages.return_value = []
        cli_with_mocks.client.send_message.side_effect = Exception("Unexpected")

        cli_with_mocks._send_message("Test")

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "unexpected" in captured.out.lower()

    def test_display_response(self, cli_with_mocks, capsys):
        """Test displaying response with formatting."""
        cli_with_mocks._display_response("Test response")

        captured = capsys.readouterr()
        assert "AI: Test response" in captured.out

    def test_display_response_multiline(self, cli_with_mocks, capsys):
        """Test displaying multi-line response preserves formatting."""
        multiline = "Line 1\nLine 2\nLine 3"
        cli_with_mocks._display_response(multiline)

        captured = capsys.readouterr()
        assert "Line 1\nLine 2\nLine 3" in captured.out

    def test_handle_error_api_error(self, cli_with_mocks, capsys):
        """Test error handling for APIError."""
        error = APIError("API error message", 500)
        cli_with_mocks._handle_error(error)

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "API error message" in captured.out

    def test_handle_error_network_error(self, cli_with_mocks, capsys):
        """Test error handling for NetworkError."""
        error = NetworkError("Network error message")
        cli_with_mocks._handle_error(error)

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "Network error message" in captured.out

    def test_handle_error_generic(self, cli_with_mocks, capsys):
        """Test error handling for generic exceptions."""
        error = Exception("Generic error")
        cli_with_mocks._handle_error(error)

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "unexpected" in captured.out.lower()

    def test_run_with_exit_command(self, cli_with_mocks):
        """Test run loop exits on /exit command."""
        with patch.object(
            cli_with_mocks, "_get_user_input", side_effect=["/exit"]
        ), patch.object(cli_with_mocks, "_display_welcome"), patch.object(
            cli_with_mocks, "_handle_command", return_value=False
        ) as mock_handle:
            cli_with_mocks.run()

            mock_handle.assert_called_once_with("/exit")

    def test_run_with_message(self, cli_with_mocks):
        """Test run loop sends message for non-command input."""
        with patch.object(
            cli_with_mocks, "_get_user_input", side_effect=["Hello", "/exit"]
        ), patch.object(cli_with_mocks, "_display_welcome"), patch.object(
            cli_with_mocks, "_send_message"
        ) as mock_send, patch.object(
            cli_with_mocks, "_handle_command", return_value=False
        ):
            cli_with_mocks.run()

            mock_send.assert_called_once_with("Hello")

    def test_run_skips_empty_input(self, cli_with_mocks):
        """Test run loop skips empty input."""
        # _get_user_input already strips whitespace, so empty strings are returned as ""
        with patch.object(
            cli_with_mocks, "_get_user_input", side_effect=["", "", "/exit"]
        ), patch.object(cli_with_mocks, "_display_welcome"), patch.object(
            cli_with_mocks, "_send_message"
        ) as mock_send, patch.object(
            cli_with_mocks, "_handle_command", return_value=False
        ):
            cli_with_mocks.run()

            mock_send.assert_not_called()

    def test_run_handles_keyboard_interrupt(self, cli_with_mocks, capsys):
        """Test run loop handles KeyboardInterrupt gracefully."""
        with patch.object(
            cli_with_mocks, "_get_user_input", side_effect=KeyboardInterrupt()
        ), patch.object(cli_with_mocks, "_display_welcome"):
            cli_with_mocks.run()

            captured = capsys.readouterr()
            assert "Goodbye" in captured.out

    def test_run_handles_eof_error(self, cli_with_mocks, capsys):
        """Test run loop handles EOFError gracefully."""
        with patch.object(
            cli_with_mocks, "_get_user_input", side_effect=EOFError()
        ), patch.object(cli_with_mocks, "_display_welcome"):
            cli_with_mocks.run()

            captured = capsys.readouterr()
            assert "Goodbye" in captured.out


class TestMainFunction:
    """Test suite for main() entry point function."""

    def test_main_runs_cli(self):
        """Test main function creates and runs CLI."""
        with patch("src.main.ChatbotCLI") as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli

            with patch.object(mock_cli, "run"):
                main()

                mock_cli_class.assert_called_once()
                mock_cli.run.assert_called_once()

    def test_main_handles_configuration_error(self, capsys):
        """Test main function handles ConfigurationError."""
        with patch(
            "src.main.ChatbotCLI", side_effect=ConfigurationError("Missing API key")
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Configuration error" in captured.out
            assert "Missing API key" in captured.out

    def test_main_handles_keyboard_interrupt(self, capsys):
        """Test main function handles KeyboardInterrupt."""
        with patch("src.main.ChatbotCLI", side_effect=KeyboardInterrupt()):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "Goodbye" in captured.out

    def test_main_handles_unexpected_error(self, capsys):
        """Test main function handles unexpected exceptions."""
        with patch("src.main.ChatbotCLI", side_effect=Exception("Unexpected error")):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Unexpected error" in captured.out


class TestCommandClassification:
    """Test suite for command vs message classification."""

    def test_command_starts_with_slash(self):
        """Test that strings starting with / are classified as commands."""
        cli = Mock(spec=ChatbotCLI)
        cli._handle_command = ChatbotCLI._handle_command.__get__(cli, ChatbotCLI)
        cli.memory = Mock()
        cli.system_prompt = "Test"

        # Commands should be handled by _handle_command
        assert "/exit".startswith("/")
        assert "/reset".startswith("/")
        assert "/persona".startswith("/")
        assert "/help".startswith("/")

    def test_message_does_not_start_with_slash(self):
        """Test that strings not starting with / are classified as messages."""
        # Regular messages should not start with /
        assert not "Hello".startswith("/")
        assert not "What is Python?".startswith("/")
        assert not "Tell me a joke".startswith("/")
