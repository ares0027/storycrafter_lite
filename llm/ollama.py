import json
from typing import Tuple, Dict, Any, List
import requests
import config
from .base import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self):
        # Default Ollama port is 11434
        url = config.LLM_BASE_URL.rstrip('/')
        if url.endswith('/api'):
            url = url[:-4]
        self.base_url = url
        self.model = config.LLM_MODEL_NAME

    def get_models(self) -> List[str]:
        try:
            url = f"{self.base_url}/api/tags"
            print(f"[DEBUG Ollama] Fetching models from: {url}")
            response = requests.get(url)
            print(f"[DEBUG Ollama] Response status code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                models_list = [m["name"] for m in data.get("models", [])]
                print(f"[DEBUG Ollama] Successfully found {len(models_list)} models: {models_list}")
                return models_list
            print(f"[DEBUG Ollama] Failed to fetch. Status: {response.status_code}, Body: {response.text}")
            return [self.model]
        except Exception as e:
            print(f"[DEBUG Ollama] Error fetching models from Ollama: {e}")
            return [self.model]

    def check_connection(self) -> bool:
        try:
            res = requests.get(f"{self.base_url}/api/version", timeout=3.0)
            return res.status_code == 200
        except:
            return False

    def unload_model(self) -> bool:
        payload = {
            "model": self.model,
            "keep_alive": 0
        }
        try:
            res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=3.0)
            return res.status_code == 200
        except:
            return False

    def process_text(self, text: str) -> Tuple[str, Dict[str, Any], int, int]:
        system_prompt = config.EXTRACTOR_SYSTEM_PROMPT
        
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nHere is the text:\n\n{text}",
            "stream": False,
            "format": "json"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data.get("response", "{}")
                
                # Ollama returns eval_count and prompt_eval_count
                tokens_sent = data.get("prompt_eval_count", 0)
                tokens_received = data.get("eval_count", 0)
                
                result = json.loads(content)
                return result.get("corrected_text", text), result.get("metadata", {}), tokens_sent, tokens_received
            else:
                print(f"Ollama error: {response.text}")
                return text, {}, 0, 0
                
            result = json.loads(content)
            return result.get("corrected_text", text), result.get("metadata", {}), tokens_sent, tokens_received
        except Exception as e:
            print(f"Error communicating with Ollama: {e}")
            return text, {}, 0, 0

    def process_custom_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "format": "json"
        }
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data.get("response", "{}")
                return json.loads(content)
            return {}
        except Exception as e:
            print(f"Error in process_custom_json (Ollama): {e}")
            return {}
