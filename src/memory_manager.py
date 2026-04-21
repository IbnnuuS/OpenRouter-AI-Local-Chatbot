"""Conversation history persistence for the OpenRouter CLI Chatbot.

This module provides the MemoryManager class for loading, saving, and managing
conversation history with file system persistence. It handles JSON serialization,
atomic writes, and graceful error handling.
"""

import json
import os
import tempfile
from typing import Dict, List

from .config import Config


class MemoryManager:
    """Manages conversation history persistence.

    The MemoryManager handles loading conversation history from a JSON file,
    maintaining it in memory during the session, and saving changes atomically
    to prevent data corruption. It validates message structure and handles
    missing or corrupted files gracefully.

    Attributes:
        config: Configuration object containing file paths and settings
        messages: List of message dictionaries with 'role' and 'content' keys
    """

    def __init__(self, config: Config):
        """Initialize memory manager with configuration.

        Args:
            config: Configuration object with memory_file_path setting
        """
        self.config = config
        self.messages: List[Dict[str, str]] = []
        self.load()

    def load(self) -> None:
        """Load conversation history from memory.json.

        Attempts to load conversation history from the configured memory file.
        If the file doesn't exist, initializes an empty conversation history.
        If the file contains invalid JSON or invalid message structure,
        initializes an empty history and logs an error.

        The method is called automatically during initialization and can be
        called manually to reload history from disk.
        """
        memory_file = self.config.memory_file_path

        # If file doesn't exist, initialize empty history
        if not os.path.exists(memory_file):
            self.messages = []
            print(
                "Info: Memory file '{}' not found. "
                "Starting with empty history.".format(memory_file)
            )
            return

        try:
            # Read and parse JSON file
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract messages array
            messages = data.get("messages", [])

            # Validate message structure
            if not self._validate_message_structure(messages):
                print(
                    "Error: Memory file '{}' contains invalid message structure. "
                    "Starting with empty history.".format(memory_file)
                )
                self.messages = []
                return

            # Store loaded messages
            self.messages = messages

        except json.JSONDecodeError as e:
            print(
                "Error: Memory file '{}' contains invalid JSON: {}. "
                "Starting with empty history.".format(memory_file, e)
            )
            self.messages = []
        except Exception as e:
            print(
                "Error: Failed to load memory file '{}': {}. "
                "Starting with empty history.".format(memory_file, e)
            )
            self.messages = []

    def save(self) -> None:
        """Save current conversation history to memory.json.

        Saves the current conversation history to the configured memory file
        using atomic writes to prevent corruption. The method writes to a
        temporary file first, then renames it to the target file, ensuring
        that the file is never left in a partially written state.

        If the save operation fails, logs an error but continues with the
        in-memory state to prevent data loss during the current session.
        """
        memory_file = self.config.memory_file_path

        try:
            # Create JSON structure
            data = {"messages": self.messages}

            # Get directory for temporary file
            memory_dir = os.path.dirname(memory_file) or "."

            # Atomic write: write to temp file, then rename
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=memory_dir, delete=False, suffix=".tmp"
            ) as temp_file:
                json.dump(data, temp_file, indent=2, ensure_ascii=False)
                temp_file_path = temp_file.name

            # Rename temp file to target file (atomic on POSIX systems)
            os.replace(temp_file_path, memory_file)

        except Exception as e:
            print("Error: Failed to save memory file '{}': {}".format(memory_file, e))
            # Continue with in-memory state; don't crash

    def append(self, role: str, content: str) -> None:
        """Append a message to conversation history and save.

        Adds a new message to the conversation history with the specified
        role and content, then immediately saves to disk to prevent data loss.

        Args:
            role: Message role ('system', 'user', or 'assistant')
            content: Message content text
        """
        message = {"role": role, "content": content}
        self.messages.append(message)
        self.save()

    def clear(self) -> None:
        """Clear all conversation history and save empty state.

        Removes all messages from the conversation history and saves the
        empty state to disk. This is typically called when the user executes
        the /reset command.
        """
        self.messages = []
        self.save()

    def get_messages(self) -> List[Dict[str, str]]:
        """Get current conversation history.

        Returns a copy of the current conversation history to prevent
        external modifications to the internal state.

        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        return self.messages.copy()

    def _validate_message_structure(self, messages: List) -> bool:
        """Validate loaded messages have correct structure.

        Checks that the messages parameter is a list and that each message
        has the required 'role' and 'content' keys with appropriate values.

        Args:
            messages: List to validate as message array

        Returns:
            True if messages have valid structure, False otherwise
        """
        # Check if messages is a list
        if not isinstance(messages, list):
            return False

        # Check each message structure
        for message in messages:
            # Must be a dictionary
            if not isinstance(message, dict):
                return False

            # Must have 'role' and 'content' keys
            if "role" not in message or "content" not in message:
                return False

            # Role must be a string and one of the valid values
            role = message["role"]
            if not isinstance(role, str):
                return False
            if role not in ("system", "user", "assistant"):
                return False

            # Content must be a string
            if not isinstance(message["content"], str):
                return False

        return True
