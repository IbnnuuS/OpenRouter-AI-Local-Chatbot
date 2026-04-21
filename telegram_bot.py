#!/usr/bin/env python3
"""
Telegram Bot integration for OpenRouter CLI Chatbot
Uses the same core modules (config, client, memory) as CLI version
"""

import logging
import os
from dotenv import load_dotenv  # Add this import
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Import our existing modules
from src.config import Config
from src.openrouter_client import OpenRouterClient
from src.memory_manager import MemoryManager
from src.exceptions import APIError, NetworkError, TimeoutError as ChatbotTimeoutError

# Load environment variables first
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramChatbot:
    """Telegram bot using OpenRouter API with same core modules as CLI"""
    
    def __init__(self):
        """Initialize bot with same components as CLI"""
        # Load config (same as CLI)
        self.config = Config.load_from_env()
        self.config.validate()
        
        # Initialize components (same as CLI)
        self.client = OpenRouterClient(self.config)
        self.memory = MemoryManager(self.config)
        
        # Load system prompt (same as CLI)
        self.system_prompt = self._load_system_prompt()
        
        logger.info("✅ Telegram bot initialized successfully")
        logger.info(f"📡 Using model: {self.config.openrouter_model}")
    
    def _load_system_prompt(self) -> str:
        """Load system prompt (Telegram-specific version if available)"""
        # Try Telegram-specific prompt first
        telegram_prompt_file = "system_prompt_telegram.txt"
        if os.path.exists(telegram_prompt_file):
            try:
                with open(telegram_prompt_file, 'r', encoding='utf-8') as f:
                    logger.info("Using Telegram-specific system prompt")
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read Telegram system prompt: {e}")
        
        # Fallback to regular system prompt
        prompt_file = self.config.system_prompt_file_path
        
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read system prompt: {e}")
                return self.config.default_system_prompt
        else:
            logger.info("System prompt file not found, using default")
            return self.config.default_system_prompt
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_text = """
🤖 **Welcome to OpenRouter AI Bot!**

I'm powered by OpenRouter API and can help you with:
• General questions and conversations
• Programming and coding help
• Creative writing and brainstorming
• And much more!

**Available commands:**
/start - Show this welcome message
/reset - Clear conversation history
/persona - Show my current personality
/help - Show available commands

Just send me a message to start chatting! 💬
        """
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown'
        )
        logger.info(f"User {update.effective_user.id} started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 **Available Commands:**

/start - Welcome message
/reset - Clear conversation history
/persona - Show AI personality
/help - Show this help

**How to use:**
Just send me any message and I'll respond using AI! 

**Examples:**
• "What is Python?"
• "Write a poem about cats"
• "Help me debug this code: [your code]"
• "Explain quantum physics simply"

**Model:** `{}`
        """.format(self.config.openrouter_model)
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reset command (same logic as CLI)"""
        self.memory.clear()
        await update.message.reply_text(
            "🗑️ **Conversation history cleared!**\n\nWe can start fresh now. What would you like to talk about?",
            parse_mode='Markdown'
        )
        logger.info(f"User {update.effective_user.id} reset conversation")
    
    async def persona_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /persona command (same logic as CLI)"""
        persona_text = f"""
🎭 **Current AI Personality:**

```
{self.system_prompt}
```

**Model:** `{self.config.openrouter_model}`
        """
        
        await update.message.reply_text(persona_text, parse_mode='Markdown')
    
    def _clean_response_for_telegram(self, response: str) -> str:
        """Clean AI response for better Telegram formatting"""
        import re
        
        # Remove problematic markdown characters
        cleaned = response
        
        # Remove markdown headers and replace with simple emphasis
        cleaned = re.sub(r'^#{1,6}\s+(.+)$', r'🔹 \1', cleaned, flags=re.MULTILINE)
        
        # Convert bold markdown to simple emphasis
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'• \1', cleaned)
        
        # Convert italic to simple text
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
        
        # Handle tables - convert to readable list format
        lines = cleaned.split('\n')
        cleaned_lines = []
        in_table = False
        table_headers = []
        
        for line in lines:
            # Skip table separator lines
            if '|' in line and '---' in line:
                continue
                
            # Handle table rows
            if '|' in line and line.count('|') >= 2:
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                
                if not in_table and cells:
                    # First row - treat as headers
                    table_headers = cells
                    cleaned_lines.append('\n📊 Informasi Detail:')
                    in_table = True
                elif cells and len(cells) >= 2:
                    # Data rows
                    if len(table_headers) >= 2:
                        cleaned_lines.append(f'• {table_headers[0]}: {cells[0]}')
                        if len(cells) > 1:
                            cleaned_lines.append(f'  └ {table_headers[1]}: {cells[1]}')
                    else:
                        cleaned_lines.append(f'• {cells[0]}: {cells[1] if len(cells) > 1 else ""}')
            else:
                if in_table and line.strip() == '':
                    in_table = False
                    cleaned_lines.append('')  # Add spacing after table
                elif not (in_table and line.strip() == ''):
                    cleaned_lines.append(line)
        
        cleaned = '\n'.join(cleaned_lines)
        
        # Clean up code blocks
        cleaned = re.sub(r'```[\w]*\n(.*?)\n```', r'💻 Code:\n\1', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'`([^`]+)`', r'"\1"', cleaned)
        
        # Clean up list formatting
        cleaned = re.sub(r'^[\-\*]\s+', '• ', cleaned, flags=re.MULTILINE)
        
        # Remove excessive newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Add some emojis for better readability
        cleaned = re.sub(r'^(\d+\.)\s+', r'🔸 ', cleaned, flags=re.MULTILINE)
        
        # Clean up any remaining problematic characters
        cleaned = cleaned.replace('**', '')
        cleaned = cleaned.replace('__', '')
        
        return cleaned.strip()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages (same logic as CLI)"""
        user_message = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"User {user_id}: {user_message}")
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, 
            action='typing'
        )
        
        try:
            # Same logic as CLI: append user message
            self.memory.append('user', user_message)
            
            # Same logic as CLI: prepare messages with system prompt
            conversation = self.memory.get_messages()
            messages = [
                {'role': 'system', 'content': self.system_prompt}
            ]
            messages.extend(conversation)
            
            # Same logic as CLI: send to API
            response = self.client.send_message(messages)
            
            # Same logic as CLI: save assistant response
            self.memory.append('assistant', response)
            
            # Clean response for Telegram formatting
            cleaned_response = self._clean_response_for_telegram(response)
            
            # Send response to user (plain text, no markdown)
            await update.message.reply_text(cleaned_response)
            
            logger.info(f"Response sent to user {user_id}")
            
        except APIError as e:
            error_msg = f"🚫 **API Error:** {str(e)}"
            await update.message.reply_text(error_msg, parse_mode='Markdown')
            logger.error(f"API error for user {user_id}: {e}")
            
        except NetworkError as e:
            error_msg = f"🌐 **Network Error:** {str(e)}"
            await update.message.reply_text(error_msg, parse_mode='Markdown')
            logger.error(f"Network error for user {user_id}: {e}")
            
        except ChatbotTimeoutError as e:
            error_msg = f"⏰ **Timeout Error:** {str(e)}"
            await update.message.reply_text(error_msg, parse_mode='Markdown')
            logger.error(f"Timeout error for user {user_id}: {e}")
            
        except Exception as e:
            error_msg = f"❌ **Unexpected Error:** An error occurred. Please try again."
            await update.message.reply_text(error_msg, parse_mode='Markdown')
            logger.error(f"Unexpected error for user {user_id}: {e}")

def main():
    """Run the Telegram bot"""
    # Get Telegram bot token from environment
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not telegram_token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment variables")
        print("Please add TELEGRAM_BOT_TOKEN to your .env file")
        return
    
    # Initialize bot
    try:
        chatbot = TelegramChatbot()
        
        # Create application
        application = Application.builder().token(telegram_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", chatbot.start_command))
        application.add_handler(CommandHandler("help", chatbot.help_command))
        application.add_handler(CommandHandler("reset", chatbot.reset_command))
        application.add_handler(CommandHandler("persona", chatbot.persona_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chatbot.handle_message))
        
        # Start bot
        print("🤖 Starting Telegram bot...")
        print(f"📡 Using model: {chatbot.config.openrouter_model}")
        print("✅ Bot is running! Press Ctrl+C to stop.")
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")

if __name__ == '__main__':
    main()