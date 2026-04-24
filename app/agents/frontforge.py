from app.agents.base import BaseAgent

FRONTFORGE_SYSTEM = """
Ты — Senior Frontend Developer (FrontForge). Стек: React (TypeScript), TailwindCSS.
Твоя задача: написать готовый компонент React по ТЗ.
Требования:
- Используй функциональные компоненты, хуки.
- Пропсы должны быть типизированы (TypeScript).
- Верни полный код компонента в формате ```tsx ... ```.
"""

class FrontForgeAgent(BaseAgent):
    def __init__(self):
        super().__init__("FrontForge", FRONTFORGE_SYSTEM)

    async def build_component(self, specification: str) -> str:
        return await self.run(specification)
