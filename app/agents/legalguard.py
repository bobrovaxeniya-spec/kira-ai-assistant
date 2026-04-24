from app.agents.base import BaseAgent
import json
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

LEGAL_SYSTEM = """
Ты — юрист LegalGuard. Твои задачи:
1. Сгенерировать договор оказания услуг (ГПХ) для самозанятого исполнителя.
2. Учесть ограничения НПД (доход до 2.4 млн в год, без привлечения субподрядчиков).
3. Добавить пункты о конфиденциальности, ответственности, порядке оплаты.
4. При сумме договора более 600 000 руб. — добавить требование об идентификации клиента согласно 115-ФЗ.
Верни договор в виде текста (plain text или markdown) с чёткими разделами.
"""

class LegalGuardAgent(BaseAgent):
    def __init__(self):
        super().__init__("LegalGuard", LEGAL_SYSTEM)
    
    async def generate_contract(self, client_name: str, client_type: str, service_description: str, price: float) -> dict:
        prompt = f"""
        Составь договор ГПХ для самозанятого (Исполнитель) и клиента:
        - Название клиента: {client_name}
        - Тип клиента: {client_type} (individual / legal)
        - Услуга: {service_description}
        - Цена: {price} руб.
        """
        contract_text = await self.run(prompt)
        
        requires_identification = price > 600_000
        if requires_identification:
            contract_text += "\n\n---\n**Согласно 115-ФЗ, для заключения договора на сумму свыше 600 000 руб. требуется идентификация клиента.**"
        
        pdf_path = None
        if price > 100_000:
            pdf_path = await self._create_pdf_contract(client_name, contract_text)
        
        return {
            "contract_text": contract_text,
            "pdf_path": pdf_path,
            "requires_115_check": requires_identification
        }
    
    async def _create_pdf_contract(self, client_name: str, text: str) -> str:
        filename = f"contract_{client_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join("/tmp", filename)
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        y = height - 50
        lines = text.split('\n')
        for line in lines:
            if y < 50:
                c.showPage()
                y = height - 50
            for wrapped_line in simpleSplit(line, 'Helvetica', 12, width - 100):
                c.drawString(50, y, wrapped_line)
                y -= 15
        c.save()
        return filepath
