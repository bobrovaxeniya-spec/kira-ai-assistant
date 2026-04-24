import asyncio
from typing import Any

from app.agents.base import BaseAgent
from logger_config import logger
from app.session_store import store

KIRA_SYSTEM = """
Ты — Кира, AI-архитектор с ироничным и дерзким характером. Продаёшь услуги автоматизации: боты, интеграции CRM, нейрофотосессии.
Выявляй боли клиента, задавай вопросы, собирай требования для ТЗ.
Отвечай коротко, остроумно, но профессионально.
"""


class SalesMindAgent(BaseAgent):
    """Sales lead collection agent with persistent session storage.

    Stores minimal collected fields (name, email) under key `salesmind:{user_id}`
    in the session store. The store is Redis-backed when REDIS_URL is set and
    aioredis is available, otherwise an in-memory fallback is used.
    """

    def __init__(self, user_id: str):
        super().__init__("Kira", KIRA_SYSTEM)
        self.user_id = user_id
        self._key = f"salesmind:{self.user_id}"

    async def _load(self) -> dict[str, Any]:
        raw = await store.get(self._key)  # type: ignore
        if not raw:
            return {}
        try:
            import json

            return json.loads(raw)
        except Exception:
            return {}

    async def _save(self, data: dict[str, Any]):
        import json

        await store.set(self._key, json.dumps(data))  # type: ignore

    async def run(self, user_message: str, context: str | None = None) -> str:
        state = await self._load()

        # Small stateful flow: collect name then email
        if not state.get("name"):
            state["name"] = user_message.strip()
            await self._save(state)
            return "Отлично, а какой у вас email?"

        if not state.get("email"):
            state["email"] = user_message.strip()
            await asyncio.sleep(0.1)
            await self._save(state)
            return "Спасибо! Я сохранил контакт и передам лид команде."

        # If both name and email present, return a closing message
        return "Спасибо — мы свяжемся с вами!"
