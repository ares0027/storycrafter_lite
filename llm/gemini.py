import json
from typing import Tuple, Dict, Any, List
import requests
import os
import config
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = config.LLM_MODEL_NAME if "gemini" in config.LLM_MODEL_NAME.lower() else "gemini-1.5-pro-latest"

    def get_models(self) -> List[str]:
        # Return common gemini models for now
        return ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest"]

    def check_connection(self) -> bool:
        if not self.api_key:
            return False
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
        try:
            res = requests.get(url, timeout=3.0)
            return res.status_code == 200
        except:
            return False

    def unload_model(self) -> bool:
        # Cloud API, no local model to unload
        return True

    def process_text(self, text: str) -> Tuple[str, Dict[str, Any], int, int]:
        if not self.api_key:
            print("GEMINI_API_KEY is not set.")
            return text, {}, 0, 0
            
        system_prompt = config.EXTRACTOR_SYSTEM_PROMPT
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_prompt}\n\nHere is the text:\n\n{text}"}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                
                # Extract text
                content_text = data["candidates"][0]["content"]["parts"][0]["text"]
                
                # Usage
                usage = data.get("usageMetadata", {})
                tokens_sent = usage.get("promptTokenCount", 0)
                tokens_received = usage.get("candidatesTokenCount", 0)
                
                result = json.loads(content_text)
                return result.get("corrected_text", text), result.get("metadata", {}), tokens_sent, tokens_received
            else:
                print(f"Gemini error: {response.text}")
                return text, {}, 0, 0
        except Exception as e:
            print(f"Error communicating with Gemini: {e}")
            return text, {}, 0, 0

    def process_custom_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(
                f"{system_prompt}\n\n{user_prompt}",
                generation_config={"response_mime_type": "application/json"}
            )
            content = response.text
            return json.loads(content)
        except Exception as e:
            print(f"Error in process_custom_json (Gemini): {e}")
            return {}
