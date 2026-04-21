#!/usr/bin/env python3
"""
Quick test of the OpenRouter API connection
"""

from src.config import Config
from src.openrouter_client import OpenRouterClient

def test_api():
    """Test API connection directly"""
    try:
        # Load config
        config = Config.load_from_env()
        config.validate()
        print(f"✅ Config loaded successfully")
        print(f"📡 Using model: {config.openrouter_model}")
        print(f"🔗 API URL: {config.openrouter_api_url}")
        
        # Create client
        client = OpenRouterClient(config)
        print(f"✅ Client created successfully")
        
        # Test message
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Please answer briefly."}
        ]
        
        print(f"📤 Sending test message...")
        response = client.send_message(messages)
        print(f"📥 Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    if success:
        print("✅ API test successful!")
    else:
        print("❌ API test failed!")