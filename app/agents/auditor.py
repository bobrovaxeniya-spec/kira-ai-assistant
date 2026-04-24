from app.agents.base import BaseAgent
import json

AUDITOR_SYSTEM = """
Ты — бизнес-аналитик Auditor. На основе диалога с клиентом (описание процессов, болей) составь детальное ТЗ для автоматизации.
Выяви:
- Тип бизнеса
- Ключевые проблемы (потери времени)
- Желаемые решения (боты, интеграции, AI-агенты)
- Бюджет (если указан)
- Сроки
Верни ТЗ в формате JSON:
{
  "business_type": "...",
  "pain_points": ["пункт1", "пункт2"],
  "solutions": ["бот", "интеграция CRM"],
  "budget": число,
  "deadline": "срок",
  "technical_requirements": "подробное описание"
}
"""

class AuditorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Auditor", AUDITOR_SYSTEM)

    async def audit(self, conversation_history: str) -> dict:
        prompt = f"История диалога:\n{conversation_history}\nСоставь ТЗ в JSON."
        response = await self.run(prompt)
        try:
            return json.loads(response)
        except:
            return {"error": "Не удалось распарсить ТЗ", "raw": response}
