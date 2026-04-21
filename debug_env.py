#!/usr/bin/env python3
"""
Debug script to check environment variables
"""

import os
from dotenv import load_dotenv

def debug_env():
    """Debug environment variables"""
    print("🔍 Debugging environment variables...")
    
    # Load .env file
    load_dotenv()
    
    # Check OpenRouter API key
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if openrouter_key:
        print(f"✅ OPENROUTER_API_KEY: {openrouter_key[:20]}...")
    else:
        print("❌ OPENROUTER_API_KEY: Not found")
    
    # Check Telegram token
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if telegram_token:
        print(f"✅ TELEGRAM_BOT_TOKEN: {telegram_token[:20]}...")
    else:
        print("❌ TELEGRAM_BOT_TOKEN: Not found")
    
    # Check model
    model = os.getenv('OPENROUTER_MODEL')
    if model:
        print(f"✅ OPENROUTER_MODEL: {model}")
    else:
        print("❌ OPENROUTER_MODEL: Not found")
    
    print("\n📁 Current directory:", os.getcwd())
    print("📄 .env file exists:", os.path.exists('.env'))
    
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            content = f.read()
            print(f"📝 .env file content ({len(content)} chars):")
            print("=" * 50)
            print(content)
            print("=" * 50)

if __name__ == "__main__":
    debug_env()