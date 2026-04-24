from app.agents.base import BaseAgent
import json
import httpx
import os

MARKETVIBE_SYSTEM = """
Ты — маркетолог MarketVibe. На основе успешного завершённого проекта (кейса) напиши пост для Telegram / LinkedIn / VK.
Пост должен быть цепляющим, с упоминанием экономии времени/денег, с хештегами.
Верни JSON:
{
  "platform": "telegram",
  "content": "текст поста",
  "hashtags": "#AI #автоматизация",
  "image_prompt": "описание для генерации изображения (опционально)"
}
"""

class MarketVibeAgent(BaseAgent):
    def __init__(self):
        super().__init__("MarketVibe", MARKETVIBE_SYSTEM)
        self.pending_posts = []  # в реальности хранить в БД

    async def generate_post(self, case_study: str) -> dict:
        response = await self.run(case_study)
        try:
            return json.loads(response)
        except:
            return {"platform": "telegram", "content": response, "hashtags": "#AI"}

    async def request_approval(self, post_data: dict, admin_chat_id: str):
        """Отправляет пост на согласование в Telegram админу"""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            return {"error": "No bot token"}
        text = f"📝 *Новый пост на согласование*\n\n{post_data.get('content','')}\n\nХештеги: {post_data.get('hashtags','')}\nПлатформа: {post_data.get('platform','telegram')}"
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": admin_chat_id, "text": text, "parse_mode": "Markdown"}
            )
        return {"status": "sent"}
