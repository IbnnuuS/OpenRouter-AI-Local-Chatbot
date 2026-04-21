#!/usr/bin/env python3
"""
Manual test simulation for CLI
"""

from src.main import ChatbotCLI
from unittest.mock import patch
import sys

def simulate_conversation():
    """Simulate a conversation"""
    try:
        # Create CLI instance
        cli = ChatbotCLI()
        print("✅ CLI initialized successfully")
        
        # Test system prompt loading
        print(f"📝 System prompt: {cli.system_prompt[:50]}...")
        
        # Simulate sending a message
        print("📤 Testing message sending...")
        
        # Mock user input to avoid blocking
        with patch('builtins.input', return_value='What is 2+2?'):
            user_input = cli._get_user_input()
            print(f"📥 User input: {user_input}")
            
            # Send the message
            cli._send_message(user_input)
            
        print("✅ Message sent successfully!")
        
        # Test commands
        print("📤 Testing /persona command...")
        result = cli._handle_command("/persona")
        print(f"📥 Command result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = simulate_conversation()
    if success:
        print("✅ Manual test successful!")
    else:
        print("❌ Manual test failed!")