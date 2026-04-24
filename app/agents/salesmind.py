from app.agents.base import BaseAgent
import json
import re

KIRA_SYSTEM = """
Ты — Кира, AI-архитектор с ироничным и дерзким характером. Продаёшь услуги автоматизации: боты, интеграции CRM, нейрофотосессии.
Выявляй боли клиента, задавай вопросы, собирай требования для ТЗ.
Отвечай коротко, остроумно, но профессионально.
"""

class SalesMindAgent(BaseAgent):
    def __init__(self):
        super().__init__("Kira", KIRA_SYSTEM)
        self.collected_data = {
            "business_type": None,
            "pain_points": [],
            "wanted_solutions": [],
            "budget": None,
            "deadline": None,
        }

    async def handle_message(self, user_text: str) -> str:
        # Временно просто передаём в run с контекстом собранных данных
        context = f"Собранные требования: {json.dumps(self.collected_data, ensure_ascii=False)}"
        response = await self.run(user_text, context)
        # Попытка извлечь обновлённые данные из ответа (упрощённо)
        # ... (можно добавить парсинг JSON)
        return response
