
import os

# LLM Configuration
# Change these values to switch models or providers globally

# Provider options: "ollama", "openai", "anthropics", "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# Model Names
# For Ollama: "llama3", "mistral", "gemma"
# For OpenAI: "gpt-4", "gpt-3.5-turbo"
# For Gemini: "gemini-2.0-flash"
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-pro")

# Connection Settings
# Connection Settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Generation Settings
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 800000
