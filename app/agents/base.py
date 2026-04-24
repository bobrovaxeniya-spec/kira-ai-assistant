import os
from typing import Optional

import httpx
from app.http_client import get_client

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:1b")


class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt

    async def run(self, user_message: str, context: Optional[str] = None) -> str:
        full_prompt = f"{self.system_prompt}\n\n"
        if context:
            full_prompt += f"Контекст: {context}\n\n"
        full_prompt += f"Пользователь: {user_message}\nАссистент:"

        client = get_client()
        try:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": 0.7}
                }
            )
            data = response.json()
            return data.get("response", "Ошибка: нет ответа от модели")
        except httpx.HTTPError as e:
            # Log and return a friendly message; agents may override behavior
            from logger_config import logger
            logger.error(f"HTTP error during LLM call: {e}")
            return "Ошибка: не удалось получить ответ от модели"
