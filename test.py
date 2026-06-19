import traceback
import asyncio
from main import update_configuration, get_models
import config

async def test():
    try:
        print("Testing Ollama...")
        await update_configuration({'LLM_PROVIDER': 'ollama', 'LLM_BASE_URL': 'http://localhost:11434'})
        print(await get_models())
        
        print("Testing Gemini...")
        await update_configuration({'LLM_PROVIDER': 'gemini', 'LLM_BASE_URL': ''})
        print(await get_models())
    except Exception as e:
        traceback.print_exc()

asyncio.run(test())
