from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class ClientCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None

class ClientResponse(ClientCreate):
    id: int
    created_at: datetime
    is_active: bool

class ProjectCreate(BaseModel):
    name: str
    budget: Optional[float] = None

class ProjectResponse(ProjectCreate):
    id: int
    client_id: int
    status: str
    created_at: datetime

class TechnicalTaskCreate(BaseModel):
    content: str
    structured_data: Optional[Dict] = None

class TechnicalTaskResponse(TechnicalTaskCreate):
    id: int
    project_id: int
    version: int
    created_at: datetime
    is_current: bool

class TaskCreate(BaseModel):
    project_id: Optional[int]
    task_type: str
    assigned_agent: str
    input_data: str

class TaskResponse(TaskCreate):
    id: int
    project_id: int
    output_data: Optional[str]
    status: str
    iteration: int
    created_at: datetime
    completed_at: Optional[datetime]
