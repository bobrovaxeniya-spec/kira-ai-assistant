from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "ai_team",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

@celery_app.task(name="generate_code_task")
def generate_code_task(task_description: str, agent_name: str, task_id: int):
    # Заглушка — в реальности вызвать агента и обновить БД
    return {"status": "completed", "agent": agent_name, "task_id": task_id}
