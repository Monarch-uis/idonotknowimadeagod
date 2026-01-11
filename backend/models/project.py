from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ProjectBase(BaseModel):
    title: str
    author: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: str
    status: str = "active"
    last_updated: Optional[str] = None
    path: str

class ProjectList(BaseModel):
    active: List[Project]
    archived: List[Project]

class ProjectLogs(BaseModel):
    project_id: str
    logs: List[str]