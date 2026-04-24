from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import os
_CIPHER = None
try:
    from cryptography.fernet import Fernet
    _ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    _CIPHER = Fernet(_ENCRYPTION_KEY.encode()) if _ENCRYPTION_KEY else None
except Exception:
    # cryptography not installed in minimal env; continue without encryption
    _CIPHER = None

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    # encrypted columns if ENCRYPTION_KEY provided
    _email = Column('email', String(500), unique=True, nullable=True)
    _phone = Column('phone', String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)

    @property
    def email(self):
        if _CIPHER and self._email:
            try:
                return _CIPHER.decrypt(self._email.encode()).decode()
            except Exception:
                return self._email
        return self._email

    @email.setter
    def email(self, value: str):
        if _CIPHER and value:
            token = _CIPHER.encrypt(value.encode()).decode()
            self._email = token
        else:
            self._email = value

    @property
    def phone(self):
        if _CIPHER and self._phone:
            try:
                return _CIPHER.decrypt(self._phone.encode()).decode()
            except Exception:
                return self._phone
        return self._phone

    @phone.setter
    def phone(self, value: str):
        if _CIPHER and value:
            token = _CIPHER.encrypt(value.encode()).decode()
            self._phone = token
        else:
            self._phone = value

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"))
    name = Column(String(200), nullable=False)
    status = Column(String(50), default="active")  # active, completed, archived
    budget = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

class TechnicalTask(Base):
    __tablename__ = "technical_tasks"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    version = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    structured_data = Column(JSON)   # разбор ТЗ на поля
    created_at = Column(DateTime, server_default=func.now())
    is_current = Column(Boolean, default=True)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    task_type = Column(String(50), nullable=False)   # frontend, backend, audit, test, review
    assigned_agent = Column(String(100))
    input_data = Column(Text)
    output_data = Column(Text)
    status = Column(String(50), default="pending")   # pending, in_progress, done, failed
    review_comments = Column(Text)
    iteration = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    message = Column(Text, nullable=False)
    sender = Column(String(20))   # client, bot, human_support
    created_at = Column(DateTime, server_default=func.now())


class MarketingPost(Base):
    __tablename__ = "marketing_posts"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    image_url = Column(String(500))
    platform = Column(String(50))
    status = Column(String(20), default="pending_approval")
    created_at = Column(DateTime, server_default=func.now())
    approved_at = Column(DateTime)
    published_at = Column(DateTime)


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    tax_rate = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    net_amount = Column(Float, default=0.0)
    transaction_type = Column(String(20))  # 'income' or 'expense'
    client_type = Column(String(20))       # 'individual' or 'legal'
    category = Column(String(100))         # for expenses
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
