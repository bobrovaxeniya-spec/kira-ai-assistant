from app.agents.base import BaseAgent
from app.agents.backsmith import BackSmithAgent
from app.agents.frontforge import FrontForgeAgent
from app.agents.testpilot import TestPilotAgent
from app.agents.codereviewer import CodeReviewerAgent
import asyncio
import json

PROJECTCORE_SYSTEM = """
Ты — Project Manager (ProjectCore). Твоя задача: разбить общее ТЗ на подзадачи для frontend, backend и тестирования.
Верни ответ в формате JSON:
{
  "frontend_task": "описание задачи для фронта",
  "backend_task": "описание задачи для бэка",
  "test_task": "описание того, что нужно протестировать"
}
"""

class ProjectCoreAgent(BaseAgent):
    def __init__(self):
        super().__init__("ProjectCore", PROJECTCORE_SYSTEM)
        self.back = BackSmithAgent()
        self.front = FrontForgeAgent()
        self.tester = TestPilotAgent()
        self.reviewer = CodeReviewerAgent()

    async def _split_tasks(self, user_task: str) -> dict:
        """Разбиваем ТЗ на три части с помощью LLM"""
        response = await self.run(user_task)
        # Очистка возможного markdown
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        try:
            tasks = json.loads(response.strip())
        except:
            # fallback
            tasks = {
                "frontend_task": user_task,
                "backend_task": user_task,
                "test_task": user_task
            }
        return tasks

    async def execute_with_quality_loop(self, user_task: str, max_iterations=3) -> dict:
        tasks = await self._split_tasks(user_task)
        
        # Генерация черновиков
        front_code = await self.front.build_component(tasks["frontend_task"])
        back_code = await self.back.generate_api(tasks["backend_task"])
        
        # Цикл ревью для бэкенда
        for i in range(max_iterations):
            review = await self.reviewer.review(tasks["backend_task"], back_code)
            if review.get("verdict") == "APPROVED":
                break
            elif review.get("verdict") == "REVISION":
                # Отправляем исправление обратному агенту (упрощённо: просто просим переписать)
                back_code = await self.back.generate_api(
                    f"{tasks['backend_task']}\nЗамечания ревьюера: {review.get('comments', '')}\nИсправь код."
                )
            else:
                return {"error": f"Backend rejected: {review.get('comments')}"}
        
        # Аналогичный цикл для фронта (опустим для краткости, но можно сделать так же)
        # ...
        
        # Генерация тестов
        combined_code = f"{back_code}\n{front_code}"
        tests = await self.tester.write_tests(combined_code)
        
        return {
            "frontend_code": front_code,
            "backend_code": back_code,
            "tests": tests,
            "status": "ready"
        }
