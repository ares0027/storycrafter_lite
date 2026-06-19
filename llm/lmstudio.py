import json
from typing import Tuple, Dict, Any, List
from openai import OpenAI, AsyncOpenAI
import config
from .base import LLMProvider

class LMStudioProvider(LLMProvider):
    def __init__(self):
        self.client = OpenAI(
            base_url=f"{config.LLM_BASE_URL.rstrip('/')}",
            api_key="lm-studio"
        )
        self.async_client = AsyncOpenAI(
            base_url=f"{config.LLM_BASE_URL.rstrip('/')}",
            api_key="lm-studio"
        )
        self.model = config.LLM_MODEL_NAME

    def get_models(self) -> List[str]:
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            print(f"Error fetching models from LM Studio: {e}")
            return [self.model]

    def check_connection(self) -> bool:
        try:
            self.client.models.list(timeout=3.0)
            return True
        except:
            return False

    def unload_model(self) -> bool:
        try:
            import requests
            requests.post(f"{self.client.base_url}/internal/model/unload", timeout=3.0)
            return True
        except:
            return False

    def process_text(self, text: str) -> Tuple[str, Dict[str, Any], int, int]:
        system_prompt = config.EXTRACTOR_SYSTEM_PROMPT
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is the text:\n\n{text}"}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            usage = response.usage
            tokens_sent = usage.prompt_tokens if usage else 0
            tokens_received = usage.completion_tokens if usage else 0
            
            # Strip markdown json wrappers if present
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
                    
            content = content.strip()

            result = json.loads(content)
            return result.get("corrected_text", text), result.get("metadata", {}), tokens_sent, tokens_received
            
        except Exception as e:
            print(f"Error communicating with LM Studio: {e}")
            return text, {}, 0, 0

    def process_custom_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            content = response.choices[0].message.content
            
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            content = content.strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"Error in process_custom_json (LM Studio): {e}")
            return {}

    def process_custom_json_stream(self, system_prompt: str, user_prompt: str, chunk_callback) -> Dict[str, Any]:
        import time
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                stream=True
            )
            content = ""
            start_time = time.time()
            tokens_received = 0
            
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        content += delta
                        # Approximate token count (LM Studio doesn't reliably stream usage)
                        tokens_received = len(content) // 4
                        elapsed = time.time() - start_time
                        if chunk_callback:
                            chunk_callback(content, tokens_received, elapsed)
            
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            content = content.strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"Error in process_custom_json_stream (LM Studio): {e}")
            return {}

    def process_vision_json(self, system_prompt: str, user_prompt: str, base64_image: str) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.3
            )
            content = response.choices[0].message.content
            
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            content = content.strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"Error in process_vision_json (LM Studio): {e}")
            return {}

    def process_vision_text(self, system_prompt: str, user_prompt: str, base64_image: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in process_vision_text (LM Studio): {e}")
            return ""

    async def stream_raw_text(self, system_prompt: str, user_prompt: str):
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                stream=True
            )
            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
        except Exception as e:
            print(f"Error in stream_raw_text (LM Studio): {e}")
            yield f"Error: {e}"
