# load_llm.py

from typing import Any

from django.conf import settings
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# Load your default API keys
OPENAI_API_KEY = settings.OPENAI_API_KEY
DEEPSEEK_API_KEY = settings.DEEPSEEK_API_KEY
ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY

def load_llm(
    model_name: str,
    api_key: str,
    base_url: str = "",
    temperature: float = 0.3,
) -> Any:
    """
    Dynamically load the correct LLM client based on model name.

    Args:
        model_name (str): The model to load (e.g., 'gpt-4-turbo', 'deepseek-chat', 'claude-3', 'gemini-1.5-pro-latest').
        api_key (str): API key for the model provider.
        base_url (str, optional): Override base URL (useful for DeepSeek, custom endpoints).
        temperature (float, optional): Model creativity setting.

    Returns:
        Any: Instantiated LLM client.
    """
    if model_name.startswith("gpt-"):
        return ChatOpenAI(
            model_name=model_name,
            openai_api_key=api_key or OPENAI_API_KEY,
            temperature=temperature,
        )

    if model_name.startswith("deepseek-"):
        return ChatOpenAI(
            model_name=model_name,
            openai_api_key=api_key or DEEPSEEK_API_KEY,
            temperature=temperature,
            base_url=base_url or "https://api.deepseek.com",
        )

    if model_name.startswith("claude-"):
        return ChatAnthropic(
            model_name=model_name,
            anthropic_api_key=api_key or ANTHROPIC_API_KEY,
            temperature=temperature,
        )


    raise ValueError(f"Unknown or unsupported model: {model_name}")