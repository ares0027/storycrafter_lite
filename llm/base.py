from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, List

class LLMProvider(ABC):
    
    @abstractmethod
    def get_models(self) -> List[str]:
        """Returns a list of available models."""
        pass
        
    @abstractmethod
    def check_connection(self) -> bool:
        """Checks if the LLM provider is reachable."""
        pass

    @abstractmethod
    def unload_model(self) -> bool:
        """Unloads the current model from memory (if applicable)."""
        pass
        
    @abstractmethod
    def process_text(self, text: str) -> Tuple[str, Dict[str, Any], int, int]:
        """
        Sends text to the LLM to correct OCR and extract metadata.
        Returns:
            Tuple of:
            - corrected_text (str)
            - metadata_dict (dict)
            - tokens_sent (int)
            - tokens_received (int)
        """
        pass

    @abstractmethod
    def process_custom_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Sends a custom prompt and expects a JSON response."""
        pass
        
    @abstractmethod
    def process_vision_json(self, system_prompt: str, user_prompt: str, base64_image: str) -> Dict[str, Any]:
        """Sends an image to a Vision model and expects a JSON response."""
        pass

    @abstractmethod
    async def stream_raw_text(self, system_prompt: str, user_prompt: str):
        """Asynchronously streams raw text from the LLM."""
        pass

    def process_custom_json_stream(self, system_prompt: str, user_prompt: str, chunk_callback) -> Dict[str, Any]:
        """Sends a custom prompt, streams the response calling chunk_callback(accumulated_text, tokens, time), and expects a JSON response."""
        # Default implementation falls back to synchronous.
        import time
        start_time = time.time()
        result = self.process_custom_json(system_prompt, user_prompt)
        # We don't have true streaming here, so just send a fake chunk completion
        if chunk_callback:
            chunk_callback(str(result), 0, time.time() - start_time)
        return result
