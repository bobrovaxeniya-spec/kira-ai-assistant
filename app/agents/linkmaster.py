from app.agents.base import BaseAgent
import json

LINKMASTER_SYSTEM = """
Ты — интегратор LinkMaster. Проверяешь, что фронтенд и бэкенд корректно взаимодействуют.
Анализируй код фронта (React/TS) и бэка (FastAPI). Выяви несоответствия:
- Эндпоинты, которые вызывает фронт, должны существовать в бэке.
- Ожидаемые форматы данных (JSON) должны совпадать.
- Обработка ошибок с обеих сторон.
Верни ответ в формате JSON:
{
  "compatible": true/false,
  "issues": ["список проблем"],
  "suggestions": ["рекомендации"]
}
"""

class LinkMasterAgent(BaseAgent):
    def __init__(self):
        super().__init__("LinkMaster", LINKMASTER_SYSTEM)

    async def check_integration(self, front_code: str, back_code: str) -> dict:
        prompt = f"Фронтенд код:\n{front_code}\n\nБэкенд код:\n{back_code}"
        response = await self.run(prompt)
        try:
            return json.loads(response)
        except:
            return {"compatible": False, "issues": ["Ошибка парсинга ответа"], "suggestions": []}
