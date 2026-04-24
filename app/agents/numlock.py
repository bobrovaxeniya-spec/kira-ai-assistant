import os
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import httpx

from app.models import Transaction
from logger_config import logger


class NumLockAgent:
    """Бухгалтер для самозанятого (НПД). Учёт доходов, расходов, налогов, лимитов."""

    NPD_RATE_INDIVIDUAL = 0.04  # 4% при работе с физлицами
    NPD_RATE_LEGAL = 0.06       # 6% с юрлицами/ИП
    YEARLY_LIMIT = 2_400_000    # 2.4 млн руб. в год для самозанятости

    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    async def record_income(self, amount: float, client_type: str = "individual", project_id: int = None, description: str = "") -> Dict:
        tax_rate = self.NPD_RATE_INDIVIDUAL if client_type == "individual" else self.NPD_RATE_LEGAL
        tax_amount = round(amount * tax_rate, 2)
        net_amount = round(amount - tax_amount, 2)

        transaction = Transaction(
            amount=amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            net_amount=net_amount,
            transaction_type="income",
            client_type=client_type,
            project_id=project_id,
            description=description
        )
        self.db.add(transaction)
        await self.db.commit()
        try:
            await self.db.refresh(transaction)
        except Exception:
            pass

        year_start = datetime(datetime.now().year, 1, 1)
        total_income_this_year = await self.get_total_income_since(year_start)
        limit_exceeded = total_income_this_year > self.YEARLY_LIMIT

        if limit_exceeded:
            logger.warning(f"Годовой лимит дохода превышен! Текущий доход: {total_income_this_year} руб.")
            await self._send_alert(f"⚠️ Превышен лимит дохода самозанятого! Доход: {total_income_this_year} руб. Лимит: {self.YEARLY_LIMIT} руб.")

        return {
            "amount": amount,
            "tax": tax_amount,
            "net": net_amount,
            "yearly_total": total_income_this_year,
            "limit_exceeded": limit_exceeded
        }

    async def record_expense(self, amount: float, category: str, description: str = "") -> Dict:
        expense = Transaction(
            amount=amount,
            transaction_type="expense",
            category=category,
            description=description
        )
        self.db.add(expense)
        await self.db.commit()
        try:
            await self.db.refresh(expense)
        except Exception:
            pass
        return {"amount": amount, "category": category, "recorded": True}

    async def get_total_income_since(self, since_date: datetime) -> float:
        result = await self.db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.transaction_type == "income",
                Transaction.created_at >= since_date
            )
        )
        total = result.scalar() or 0.0
        return float(total)

    async def generate_tax_report(self, year: Optional[int] = None) -> str:
        if year is None:
            year = datetime.now().year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)

        incomes_res = await self.db.execute(
            select(Transaction).where(
                Transaction.transaction_type == "income",
                Transaction.created_at.between(start_date, end_date)
            )
        )
        incomes = incomes_res.scalars().all()

        total_income = sum(i.amount for i in incomes)
        total_tax = sum((i.tax_amount or 0.0) for i in incomes)

        report = f"📊 Налоговый отчёт за {year}\n"
        report += f"Доход: {total_income:,.2f} руб.\n"
        report += f"Налог (НПД): {total_tax:,.2f} руб.\n"
        report += f"Чистый доход: {total_income - total_tax:,.2f} руб.\n"
        report += f"Лимит самозанятости: {self.YEARLY_LIMIT:,.2f} руб.\n"
        if total_income > self.YEARLY_LIMIT:
            report += "⚠️ ВНИМАНИЕ: превышен лимит! Требуется смена налогового режима.\n"
        return report

    async def _send_alert(self, message: str):
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        admin_id = os.getenv("ADMIN_TELEGRAM_ID")
        if bot_token and admin_id:
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={"chat_id": admin_id, "text": message},
                        timeout=10.0,
                    )
                except Exception as e:
                    logger.error(f"Failed to send alert to admin: {e}")
