"""CLI interface for the OpenRouter CLI Chatbot.

This module provides the interactive command-line interface for the chatbot,
orchestrating the configuration, API client, and memory manager components.
"""

import os
import sys

from .config import Config
from .openrouter_client import OpenRouterClient
from .memory_manager import MemoryManager
from .exceptions import (
    ConfigurationError,
    APIError,
    NetworkError,
    TimeoutError as ChatbotTimeoutError,
    ResponseParseError,
)


class ChatbotCLI:
    """Interactive CLI for OpenRouter chatbot.

    This class provides the main user interface for the chatbot application,
    handling user input, command processing, message sending, and response
    display. It orchestrates the configuration, API client, and memory manager
    components to provide a seamless conversational experience.

    Attributes:
        config: Application configuration
        client: OpenRouter API client
        memory: Conversation history manager
        system_prompt: System prompt defining AI behavior
    """

    def __init__(self):
        """Initialize CLI with configuration and components.

        Loads configuration from environment, initializes the API client
        and memory manager, and loads the system prompt. If configuration
        is invalid, raises ConfigurationError.

        Raises:
            ConfigurationError: If required configuration is missing or invalid
        """
        # Load configuration
        self.config = Config.load_from_env()
        self.config.validate()

        # Initialize components
        self.client = OpenRouterClient(self.config)
        self.memory = MemoryManager(self.config)

        # Load system prompt
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load system prompt from file or use default.

        Attempts to load the system prompt from the configured file path.
        If the file doesn't exist or cannot be read, uses the default
        system prompt from configuration and logs a warning.

        Returns:
            System prompt text with formatting preserved
        """
        prompt_file = self.config.system_prompt_file_path

        # Try to read system prompt file
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    prompt = f.read()
                return prompt
            except Exception as e:
                print(
                    "Warning: Failed to read system prompt file '{}': {}".format(
                        prompt_file, e
                    )
                )
                print("Using default system prompt.")
                return self.config.default_system_prompt
        else:
            print(
                "Info: System prompt file '{}' not found. Using default.".format(
                    prompt_file
                )
            )
            return self.config.default_system_prompt

    def _display_welcome(self) -> None:
        """Display welcome message and instructions.

        Prints a welcome message with the application name and lists
        available commands for the user.
        """
        print("=" * 60)
        print("Welcome to OpenRouter CLI Chatbot!")
        print("=" * 60)
        print("\nAvailable commands:")
        print("  /exit    - Exit the chatbot")
        print("  /reset   - Clear conversation history")
        print("  /persona - Display current system prompt")
        print("  /help    - Show this help message")
        print("\nType your message and press Enter to chat.")
        print("=" * 60)
        print()

    def _get_user_input(self) -> str:
        """Get user input with prompt indicator.

        Displays the user prompt and waits for input. Strips leading
        and trailing whitespace from the input.

        Returns:
            User input string with whitespace stripped
        """
        return input("You: ").strip()

    def _handle_command(self, command: str) -> bool:
        """Handle CLI commands.

        Processes special commands that start with "/". Supported commands
        include /exit, /reset, /persona, and /help. Unknown commands display
        an error message with the list of valid commands.

        Args:
            command: User input string (should start with "/")

        Returns:
            True if should continue the main loop, False if should exit
        """
        command_lower = command.lower()

        if command_lower == "/exit":
            print("\nGoodbye! Your conversation has been saved.")
            return False

        elif command_lower == "/reset":
            self.memory.clear()
            print("\nConversation history cleared.")
            return True

        elif command_lower == "/persona":
            print("\nCurrent system prompt:")
            print("-" * 60)
            print(self.system_prompt)
            print("-" * 60)
            print()
            return True

        elif command_lower == "/help":
            print("\nAvailable commands:")
            print("  /exit    - Exit the chatbot")
            print("  /reset   - Clear conversation history")
            print("  /persona - Display current system prompt")
            print("  /help    - Show this help message")
            print()
            return True

        else:
            print(f"\nError: Unknown command '{command}'")
            print("Valid commands: /exit, /reset, /persona, /help")
            print()
            return True

    def _send_message(self, user_message: str) -> None:
        """Send user message and display response.

        Appends the user message to conversation history, prepares the
        complete message context with system prompt, sends to the API,
        displays the response, and saves the assistant's response to memory.

        Handles all API-related errors gracefully and displays user-friendly
        error messages.

        Args:
            user_message: The user's message text
        """
        # Append user message to memory
        self.memory.append("user", user_message)

        # Get conversation history
        conversation = self.memory.get_messages()

        # Prepend system prompt as first message
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(conversation)

        # Display loading indicator
        print("\nAI is thinking...")

        try:
            # Send message to API
            response = self.client.send_message(messages)

            # Display response
            self._display_response(response)

            # Append assistant response to memory
            self.memory.append("assistant", response)

        except APIError as e:
            self._handle_error(e)
        except NetworkError as e:
            self._handle_error(e)
        except ChatbotTimeoutError as e:
            self._handle_error(e)
        except ResponseParseError as e:
            self._handle_error(e)
        except Exception as e:
            self._handle_error(e)

    def _display_response(self, response: str) -> None:
        """Display assistant response with formatting.

        Prints the assistant's response with a clear label and preserves
        multi-line formatting for readability.

        Args:
            response: The assistant's response text
        """
        print(f"\nAI: {response}")
        print()

    def _handle_error(self, error: Exception) -> None:
        """Display user-friendly error message.

        Maps exception types to user-friendly error messages without
        exposing sensitive information. Logs full error details for
        debugging purposes.

        Args:
            error: The exception that occurred
        """
        print()

        if isinstance(error, APIError):
            print(f"Error: {str(error)}")
        elif isinstance(error, NetworkError):
            print(f"Error: {str(error)}")
        elif isinstance(error, ChatbotTimeoutError):
            print(f"Error: {str(error)}")
        elif isinstance(error, ResponseParseError):
            print(f"Error: Failed to parse API response. {str(error)}")
        else:
            print("Error: An unexpected error occurred. Please try again.")
            # Log full error for debugging (in production, use proper logging)
            print(f"Debug: {type(error).__name__}: {str(error)}")

        print()

    def run(self) -> None:
        """Main application loop.

        Displays the welcome message and enters the main interaction loop,
        continuously accepting user input, processing commands, and sending
        messages until the user exits. Handles keyboard interrupts gracefully.
        """
        # Display welcome message
        self._display_welcome()

        # Main interaction loop
        while True:
            try:
                # Get user input
                user_input = self._get_user_input()

                # Skip empty input
                if not user_input:
                    continue

                # Check if input is a command
                if user_input.startswith("/"):
                    # Handle command
                    should_continue = self._handle_command(user_input)
                    if not should_continue:
                        break
                else:
                    # Send message to AI
                    self._send_message(user_input)

            except KeyboardInterrupt:
                print("\n\nGoodbye! Your conversation has been saved.")
                break
            except EOFError:
                print("\n\nGoodbye! Your conversation has been saved.")
                break


def main():
    """Application entry point.

    Creates and runs the chatbot CLI. Handles configuration errors
    and unexpected exceptions gracefully, displaying appropriate error
    messages and exit codes.
    """
    try:
        cli = ChatbotCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        print("\nPlease check your .env file and ensure OPENROUTER_API_KEY is set.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
