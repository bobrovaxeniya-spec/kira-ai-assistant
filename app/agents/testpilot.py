from app.agents.base import BaseAgent

TESTPILOT_SYSTEM = """
Ты — QA Engineer (TestPilot). Пишешь unit-тесты на pytest для Python (FastAPI).
По данному коду напиши тесты, покрывающие основные сценарии и ошибки.
Верни код тестов в формате ```python ... ```.
"""

class TestPilotAgent(BaseAgent):
    def __init__(self):
        super().__init__("TestPilot", TESTPILOT_SYSTEM)

    async def write_tests(self, code_to_test: str) -> str:
        prompt = f"Напиши pytest тесты для следующего кода:\n{code_to_test}"
        return await self.run(prompt)
