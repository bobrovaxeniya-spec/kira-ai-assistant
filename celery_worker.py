from orchestrator import celery_app
from app.agents.backsmith import BackSmithAgent
from app.database import AsyncSessionLocal
from app.models import Task
import asyncio
import datetime

@celery_app.task(name="generate_code_task")
def generate_code_task(task_description: str, agent_name: str, task_id: int):
    # Запускаем асинхронную функцию внутри синхронной задачи
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(asyncio.wait_for(run_agent(task_description, agent_name, task_id), timeout=300))
    except Exception as e:
        result = {"task_id": task_id, "status": "failed", "error": str(e)}
    return result

async def run_agent(task_description: str, agent_name: str, task_id: int):
    agent = BackSmithAgent() if agent_name == "BackSmith" else None
    if not agent:
        return {"error": f"Unknown agent {agent_name}"}
    err = None
    try:
        code = await asyncio.wait_for(agent.generate_api(task_description), timeout=240)
        status = "done"
    except Exception as e:
        code = None
        status = "failed"
        err = str(e)

    # Обновляем запись в БД
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if task:
            task.status = status
            task.output_data = code
            task.completed_at = datetime.datetime.utcnow()
            await db.commit()
    if status == "failed":
        return {"task_id": task_id, "status": status, "error": err}
    return {"task_id": task_id, "status": status, "output": code}
