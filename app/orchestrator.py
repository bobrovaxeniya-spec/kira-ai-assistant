from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from celery import Celery
import os
from dotenv import load_dotenv
import time
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge
from typing import Optional

from app.database import get_db, engine
from app.models import Base
import json
from app.models import Client, Project, TechnicalTask, Task, Conversation, MarketingPost
from app.schemas import ClientCreate, ProjectCreate, TechnicalTaskCreate
from app.agents.salesmind import SalesMindAgent
from app.agents.backsmith import BackSmithAgent
from app.agents.frontforge import FrontForgeAgent
from app.agents.testpilot import TestPilotAgent
from app.agents.projectcore import ProjectCoreAgent
from app.agents.linkmaster import LinkMasterAgent
from app.agents.repomanager import RepoManagerAgent
from app.agents.auditor import AuditorAgent
from app.agents.marketvibe import MarketVibeAgent
from app.agents.datapulse import DataPulseAgent
from app.agents.numlock import NumLockAgent
from app.agents.legalguard import LegalGuardAgent

load_dotenv()

app = FastAPI(title="AI Team Orchestrator", version="2.0")


@app.get("/health")
async def health():
    return {"status": "ok"}

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Custom metrics
tasks_total = Counter('ai_tasks_total', 'Total tasks processed', ['agent', 'status'])
task_duration = Histogram('ai_task_duration_seconds', 'Task duration', ['agent'])
active_projects = Gauge('ai_active_projects', 'Number of active projects')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Celery (оставляем как было)
celery_app = Celery(
    "ai_team",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# Инициализация БД (создание таблиц) - в проде использовать alembic, но для начала автоматически
@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)  # осторожно!
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def init_http_client():
    # Ensure shared AsyncClient is created and ready
    from app.http_client import get_client
    get_client()


@app.on_event("shutdown")
async def shutdown_http_client():
    from app.http_client import close_client
    await close_client()

# Хранилище сессий Киры (временно в памяти, но можно перенести в Redis)
kira_sessions = {}

# Инициализация агентов для быстрых вызовов
backsmith = BackSmithAgent()
frontforge = FrontForgeAgent()
testpilot = TestPilotAgent()
projectcore = ProjectCoreAgent()
linkmaster = LinkMasterAgent()
repomanager = RepoManagerAgent()
auditor = AuditorAgent()
marketvibe = MarketVibeAgent()

@app.post("/webhook/chat-webhook")
async def chat_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    user_message = data.get("message", "")
    session_id = data.get("sessionId", "default")
    
    if session_id not in kira_sessions:
        kira_sessions[session_id] = SalesMindAgent()
    agent = kira_sessions[session_id]

    # SalesMindAgent exposes `run` as the main entrypoint; use it to avoid relying on
    # a non-guaranteed `handle_message` helper on the agent implementation.
    reply = await agent.run(user_message)
    
    # Сохраняем сообщения в БД (опционально)
    # conversation = Conversation(client_id=None, message=user_message, sender="client")
    # db.add(conversation)
    # await db.commit()
    
    return {"reply": reply, "sessionId": session_id}

# Новый эндпоинт для генерации кода через BackSmith (запуск в фоне через Celery)
@app.post("/generate/backend")
async def generate_backend(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    task_description = data.get("task")
    project_id = data.get("project_id")
    if not task_description:
        raise HTTPException(400, "Missing 'task' field")
    
    # Создаём задачу в БД
    new_task = Task(
        project_id=project_id,
        task_type="backend",
        assigned_agent="BackSmith",
        input_data=task_description,
        status="pending"
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # Отправляем в Celery
    celery_app.send_task("generate_code_task", args=[task_description, "BackSmith", new_task.id])
    
    return {"task_id": new_task.id, "status": "queued"}

@app.get("/task/{task_id}")
async def get_task_status(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {"status": task.status, "output": task.output_data}

# Остальные эндпоинты (для клиентов, проектов) можно добавить позже



@app.post("/generate/frontend")
async def generate_frontend(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    spec = data.get("spec") or data.get("specification") or data.get("task")
    project_id = data.get("project_id")
    if not spec:
        raise HTTPException(400, "Missing 'spec' field")
    code = await frontforge.build_component(spec)
    if project_id:
        db_task = Task(project_id=project_id, task_type="frontend", assigned_agent="FrontForge",
                       input_data=spec, output_data=(code[:1000] if code else None), status="done")
        db.add(db_task)
        await db.commit()
    return {"code": code}



@app.post("/integration/check")
async def check_integration(request: Request):
    data = await request.json()
    front_code = data.get("front_code") or data.get("front") or data.get("frontend")
    back_code = data.get("back_code") or data.get("back") or data.get("backend")
    if not front_code or not back_code:
        raise HTTPException(400, "Missing front_code or back_code")
    result = await linkmaster.check_integration(front_code, back_code)
    return result


@app.post("/repo/create")
async def create_repo(request: Request):
    data = await request.json()
    repo_name = data.get("repo_name")
    description = data.get("description", "")
    private = data.get("private", True)
    if not repo_name:
        raise HTTPException(400, "Missing 'repo_name'")
    result = await repomanager.create_repo(repo_name, description, private)
    return result


@app.post("/repo/push")
async def push_to_repo(request: Request):
    data = await request.json()
    repo_name = data.get("repo_name")
    files = data.get("files", {})
    commit_message = data.get("commit_message", "AI generated code")
    if not repo_name or not files:
        raise HTTPException(400, "Missing repo_name or files")
    result = await repomanager.push_files(repo_name, files, commit_message)
    return result


@app.post("/audit/from_conversation")
async def audit_conversation(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    client_id = data.get("client_id")
    if not client_id:
        raise HTTPException(400, "Missing client_id")
    # Проверить существование клиента
    client_obj = await db.get(Client, client_id)
    if not client_obj:
        raise HTTPException(404, "Client not found")

    # Получить последние N сообщений клиента
    convs = await db.execute(
        select(Conversation).where(Conversation.client_id == client_id).order_by(Conversation.created_at.desc()).limit(20)
    )
    conv_list = convs.scalars().all()
    history = "\n".join([f"{c.sender}: {c.message}" for c in conv_list]) if conv_list else ""
    tz = await auditor.audit(history)
    # Сохранить в БД как TechnicalTask
    project = Project(name=f"Аудит {client_id}", client_id=client_id, status="analysis")
    db.add(project)
    await db.flush()
    tech_task = TechnicalTask(project_id=project.id, content=json.dumps(tz), is_current=True)
    db.add(tech_task)
    await db.commit()
    return {"project_id": project.id, "technical_spec": tz}


@app.post("/marketing/generate_post")
async def generate_post(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    project_id = data.get("project_id")
    if not project_id:
        raise HTTPException(400, "Missing project_id")
    project = await db.get(Project, project_id)
    if not project:
        return {"error": "Project not found"}
    case_study = f"Проект {project.name} завершён. Бюджет: {project.budget}."
    post = await marketvibe.generate_post(case_study)
    # Сохранить в БД (marketing_posts table)
    mp = None
    try:
        mp = MarketingPost(content=post.get('content', ''), image_url=post.get('image_url'), platform=post.get('platform'), status='pending_approval')
        db.add(mp)
        await db.commit()
    except Exception:
        # ignore DB save errors for now
        pass
    admin_chat_id = os.getenv("ADMIN_TELEGRAM_ID")
    if admin_chat_id:
        await marketvibe.request_approval(post, admin_chat_id)
    return {"post": post, "status": "pending_approval", "db_id": (mp.id if mp else None)}


@app.get("/reports/weekly")
async def weekly_report(db: AsyncSession = Depends(get_db)):
    datapulse = DataPulseAgent(db)
    report = await datapulse.generate_weekly_report()
    return {"report": report}


@app.post("/finance/record_income")
async def record_income(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    amount = data.get("amount")
    client_type = data.get("client_type", "individual")
    project_id = data.get("project_id")
    description = data.get("description", "")
    if amount is None:
        raise HTTPException(400, "Missing 'amount'")
    numlock = NumLockAgent(db)
    result = await numlock.record_income(float(amount), client_type, project_id, description)
    return result


@app.post("/finance/record_expense")
async def record_expense(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    amount = data.get("amount")
    category = data.get("category")
    description = data.get("description", "")
    if amount is None or not category:
        raise HTTPException(400, "Missing 'amount' or 'category'")
    numlock = NumLockAgent(db)
    result = await numlock.record_expense(float(amount), category, description)
    return result


@app.get("/finance/tax_report")
async def tax_report(year: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    numlock = NumLockAgent(db)
    report = await numlock.generate_tax_report(year)
    return {"report": report}


@app.post("/legal/generate_contract")
async def generate_contract(request: Request):
    data = await request.json()
    client_name = data.get("client_name")
    client_type = data.get("client_type", "individual")
    service = data.get("service")
    price = data.get("price")
    if not client_name or not service or price is None:
        raise HTTPException(400, "Missing client_name, service or price")
    legal = LegalGuardAgent()
    contract = await legal.generate_contract(client_name, client_type, service, float(price))
    return contract


@app.post("/generate/tests")
async def generate_tests(request: Request):
    data = await request.json()
    code = data.get("code")
    if not code:
        raise HTTPException(400, "Missing 'code' field")
    tests = await testpilot.write_tests(code)
    return {"tests": tests}


@app.post("/project/execute")
async def execute_project(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    task_description = data.get("task_description") or data.get("task")
    project_name = data.get("project_name")
    client_id = data.get("client_id")
    if not task_description:
        raise HTTPException(400, "Missing 'task_description' field")

    # Создаём проект в БД
    project = Project(name=project_name or "Новый проект", client_id=client_id, status="active")
    db.add(project)
    await db.flush()
    # Сохраняем ТЗ
    tz = TechnicalTask(project_id=project.id, content=task_description, is_current=True)
    db.add(tz)
    await db.commit()
    
    # Запускаем ProjectCore (долго, поэтому через Celery? пока просто await)
    start = time.time()
    result = await projectcore.execute_with_quality_loop(task_description)
    task_duration.labels(agent='ProjectCore').observe(time.time() - start)
    tasks_total.labels(agent='ProjectCore', status='success').inc()
    # обновить gauge активных проектов
    try:
        res = await db.execute(select(func.count(Project.id)).where(Project.status == 'active'))
        cnt = res.scalar() or 0
        active_projects.set(cnt)
    except Exception:
        pass
    
    # Сохраняем результат
    for agent_name, code in [("BackSmith", result.get("backend_code")), ("FrontForge", result.get("frontend_code")), ("TestPilot", result.get("tests"))]:
        if code is None:
            continue
        db_task = Task(project_id=project.id, task_type=agent_name.lower(), assigned_agent=agent_name,
                       input_data=task_description, output_data=(code[:1000] if isinstance(code, str) else str(code)), status="done")
        db.add(db_task)
    await db.commit()
    
    return {"project_id": project.id, "result": result}
