# 🤖 OpenRouter AI Chatbot

A **modular Python chatbot** that integrates with OpenRouter API, supporting both **CLI** and **Telegram Bot** interfaces. Built with clean architecture and extensible design for easy expansion to web apps, Discord bots, and REST APIs.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![OpenRouter](https://img.shields.io/badge/OpenRouter-API-green.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ **Features**

### 🎯 **Dual Interface Support**
- **🖥️ CLI Interface** - Interactive command-line chatbot
- **📱 Telegram Bot** - Full-featured Telegram integration
- **🔄 Shared Core** - Same AI capabilities across platforms

### 🤖 **AI Capabilities**
- **29+ Free AI Models** via OpenRouter (Llama, GPT, Gemma, etc.)
- **Smart Model Router** - Automatic model selection
- **Conversation Memory** - Persistent chat history
- **Custom Personalities** - Configurable system prompts
- **Multi-turn Context** - Maintains conversation flow

### 🛠️ **Developer Features**
- **Modular Architecture** - Easy to extend and customize
- **Clean Code** - Type hints, docstrings, comprehensive tests
- **Error Handling** - Graceful network and API error recovery
- **Configuration Management** - Environment-based settings
- **Extensible Design** - Ready for web apps, Discord bots, REST APIs

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.10+
- OpenRouter API key (free at [openrouter.ai](https://openrouter.ai/keys))

### **Installation**

```bash
# Clone repository
git clone https://github.com/yourusername/openrouter-ai-chatbot.git
cd openrouter-ai-chatbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

### **🖥️ Run CLI Chatbot**

```bash
python -m src.main
```

### **📱 Run Telegram Bot**

```bash
# Get bot token from @BotFather on Telegram
# Add TELEGRAM_BOT_TOKEN to .env file
python telegram_bot.py
```

## 📖 **Usage Examples**

### **CLI Interface**
```
============================================================
Welcome to OpenRouter CLI Chatbot!
============================================================

You: What is Python?
AI is thinking...
AI: Python is a high-level programming language...

You: /persona
Current system prompt:
You are a helpful, friendly AI assistant...

You: /exit
Goodbye! Your conversation has been saved.
```

### **Telegram Bot**
```
User: /start
Bot: 🤖 Welcome to OpenRouter AI Bot!

User: Explain quantum computing
Bot: 🔹 Quantum Computing Overview
• Quantum computing uses quantum mechanics...
• Key principles include superposition...

User: /reset
Bot: 🗑️ Conversation history cleared!
```

## ⚙️ **Configuration**

### **Environment Variables**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | **Yes** | - | Your OpenRouter API key |
| `OPENROUTER_MODEL` | No | `openrouter/free` | AI model to use |
| `TELEGRAM_BOT_TOKEN` | No | - | Telegram bot token (for bot only) |
| `MEMORY_FILE_PATH` | No | `memory.json` | Conversation history file |
| `SYSTEM_PROMPT_FILE_PATH` | No | `system_prompt.txt` | AI personality file |

### **Available Models**

```bash
# Auto-select best available model (recommended)
OPENROUTER_MODEL=openrouter/free

# Specific free models
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
OPENROUTER_MODEL=openai/gpt-oss-120b:free
OPENROUTER_MODEL=google/gemma-4-31b-it:free
OPENROUTER_MODEL=qwen/qwen3-coder:free  # Great for coding
```

### **Custom System Prompts**

Edit `system_prompt.txt` to customize AI personality:

```
You are a helpful coding assistant.

Personality:
- Expert in Python and web development
- Provide clear, practical examples
- Encourage best practices
- Patient and encouraging

Focus on helping users learn programming effectively.
```

## 🏗️ **Architecture**

### **Project Structure**
```
openrouter-ai-chatbot/
├── src/
│   ├── main.py              # CLI interface
│   ├── config.py            # Configuration management
│   ├── openrouter_client.py # OpenRouter API client
│   ├── memory_manager.py    # Conversation persistence
│   └── exceptions.py        # Custom exceptions
├── telegram_bot.py          # Telegram bot interface
├── tests/                   # Comprehensive test suite
├── system_prompt.txt        # AI personality config
├── memory.json             # Conversation history
├── .env.example            # Environment template
└── requirements.txt        # Dependencies
```

### **Modular Design**

The core modules are **platform-agnostic** and reusable:

- **`config.py`** - Environment-based configuration
- **`openrouter_client.py`** - API client with retry logic
- **`memory_manager.py`** - Conversation persistence
- **`exceptions.py`** - Error handling

**Interface modules** use the same core:
- **`main.py`** - CLI-specific interface
- **`telegram_bot.py`** - Telegram-specific interface

## 🧪 **Testing**

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific tests
pytest tests/unit/test_config.py
```

**Test Coverage**: 48 unit tests with 100% pass rate

## 🔧 **Development**

### **Code Quality**
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### **Adding New Interfaces**

The modular design makes it easy to add new interfaces:

**Web App Example** (Flask):
```python
from flask import Flask, request, jsonify
from src.openrouter_client import OpenRouterClient
from src.memory_manager import MemoryManager

app = Flask(__name__)
client = OpenRouterClient(config)
memory = MemoryManager(config)

@app.route('/chat', methods=['POST'])
def chat():
    # Same core logic as CLI/Telegram
    pass
```

**Discord Bot Example**:
```python
import discord
from src.openrouter_client import OpenRouterClient

# Same core modules, different interface
```

## 🚀 **Deployment**

### **CLI Deployment**
```bash
# Local usage
python -m src.main

# Or create executable
pip install pyinstaller
pyinstaller --onefile src/main.py
```

### **Telegram Bot Deployment**

**Local:**
```bash
python telegram_bot.py
```

**Cloud (Heroku):**
```bash
# Add Procfile
echo "bot: python telegram_bot.py" > Procfile

# Deploy
git push heroku main
```

**Docker:**
```dockerfile
FROM python:3.10-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "telegram_bot.py"]
```

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### **Development Setup**
```bash
# Clone your fork
git clone https://github.com/yourusername/openrouter-ai-chatbot.git

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Ensure code quality
black src/ tests/
flake8 src/ tests/
mypy src/
```

## 📝 **Roadmap**

### **🎯 Planned Features**
- [ ] **Web Interface** (Flask/FastAPI)
- [ ] **Discord Bot** integration
- [ ] **REST API** endpoints
- [ ] **Voice Input/Output** support
- [ ] **Multi-user Memory** management
- [ ] **Conversation Export** (PDF, Markdown)
- [ ] **Plugin System** for custom commands
- [ ] **Database Backend** (PostgreSQL/SQLite)

### **🔧 Technical Improvements**
- [ ] **Async Support** for better performance
- [ ] **Streaming Responses** for real-time output
- [ ] **Rate Limiting** built-in
- [ ] **Conversation Summarization**
- [ ] **Context Window Management**
- [ ] **Multi-language Support**

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **[OpenRouter](https://openrouter.ai)** - For providing free access to AI models
- **[Telegram](https://telegram.org)** - For the excellent Bot API
- **Open Source Community** - For the amazing Python libraries

## 📞 **Support**

- **Issues**: [GitHub Issues](https://github.com/yourusername/openrouter-ai-chatbot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/openrouter-ai-chatbot/discussions)
- **Email**: your.email@example.com

---

**⭐ If you find this project helpful, please give it a star on GitHub!**

**Built with ❤️ using Python, OpenRouter API, and modern development practices.**
