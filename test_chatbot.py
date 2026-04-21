#!/usr/bin/env python3
"""
Simple test script for the OpenRouter CLI Chatbot
"""

import subprocess
import time
import sys

def test_chatbot():
    """Test the chatbot with a simple message"""
    print("🧪 Testing OpenRouter CLI Chatbot...")
    
    # Start the chatbot process
    process = subprocess.Popen(
        [sys.executable, "-m", "src.main"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # Send a test message
        test_message = "Hello! Can you tell me what 2+2 equals?\n"
        print(f"📤 Sending: {test_message.strip()}")
        
        # Send the message
        process.stdin.write(test_message)
        process.stdin.flush()
        
        # Wait a bit for response
        time.sleep(5)
        
        # Send exit command
        process.stdin.write("/exit\n")
        process.stdin.flush()
        
        # Wait for process to complete
        stdout, stderr = process.communicate(timeout=10)
        
        print("📥 Output:")
        print(stdout)
        
        if stderr:
            print("❌ Errors:")
            print(stderr)
            
        return process.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        process.kill()
        return False

if __name__ == "__main__":
    success = test_chatbot()
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")
    sys.exit(0 if success else 1)