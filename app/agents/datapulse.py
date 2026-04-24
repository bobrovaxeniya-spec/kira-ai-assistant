from sqlalchemy import select, func
from app.models import Project, Task



class DataPulseAgent:
    def __init__(self, db):
        self.db = db

    async def get_metrics(self) -> dict:
        # Количество проектов
        total_projects_res = await self.db.execute(select(func.count(Project.id)))
        total_projects = total_projects_res.scalar()
        # Количество задач по статусам
        tasks_status_res = await self.db.execute(select(Task.status, func.count(Task.id)).group_by(Task.status))
        rows = tasks_status_res.all()
        status_counts = {row[0]: row[1] for row in rows}
        return {
            "total_projects": total_projects,
            "tasks_status": status_counts,
        }

    async def generate_weekly_report(self) -> str:
        metrics = await self.get_metrics()
        # Lightweight textual report; heavy visualization libs are optional
        report = f"📊 Отчёт за неделю\nПроектов: {metrics['total_projects']}\n"
        for status, count in metrics['tasks_status'].items():
            report += f"Задач со статусом {status}: {count}\n"
        return report
