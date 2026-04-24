import json
from app.agents.base import BaseAgent

CODE_REVIEW_SYSTEM = """
Ты — строгий Code Reviewer. Проверь код по критериям:
- Соответствие ТЗ
- Безопасность (SQL injection, XSS)
- Обработка ошибок
- Читаемость и стиль (PEP8)
- Производительность

Верни ответ в формате JSON:
{
  "verdict": "APPROVED" | "REVISION" | "REJECT",
  "comments": "список замечаний с указанием строк",
  "suggestions": "предложения по исправлению"
}
"""

class CodeReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__("CodeReviewer", CODE_REVIEW_SYSTEM)

    async def review(self, task_description: str, code: str) -> dict:
        prompt = f"ТЗ: {task_description}\n\nКод:\n{code}"
        response = await self.run(prompt)
        # Пытаемся распарсить JSON
        try:
            return json.loads(response)
        except:
            # fallback
            return {"verdict": "REVISION", "comments": response, "suggestions": ""}
