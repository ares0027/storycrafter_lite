import config
from .base import LLMProvider
from .lmstudio import LMStudioProvider
from .ollama import OllamaProvider
from .gemini import GeminiProvider

def get_llm_provider() -> LLMProvider:
    """Returns the configured LLM provider instance."""
    provider = config.LLM_PROVIDER.lower()
    
    if provider == "lmstudio":
        return LMStudioProvider()
    elif provider == "ollama":
        return OllamaProvider()
    elif provider == "gemini":
        return GeminiProvider()
    else:
        # Default fallback
        print(f"Unknown provider '{provider}', falling back to LM Studio")
        return LMStudioProvider()
