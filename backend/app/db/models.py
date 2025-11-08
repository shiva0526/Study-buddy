from sqlmodel import SQLModel, Field
from datetime import datetime, date
from typing import Optional
import uuid

def gen_id():
    return str(uuid.uuid4())

class User(SQLModel, table=True):
    id: str = Field(default_factory=gen_id, primary_key=True)
    username: str
    xp: int = 0
    level: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Plan(SQLModel, table=True):
    id: str = Field(default_factory=gen_id, primary_key=True)
    user_id: str
    subject: str
    exam_date: Optional[date]
    status: str = "indexing"
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Resource(SQLModel, table=True):
    id: str = Field(default_factory=gen_id, primary_key=True)
    plan_id: str
    filename: str
    filepath: str
    type: Optional[str] = "notes"
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class Chunk(SQLModel, table=True):
    id: str = Field(default_factory=gen_id, primary_key=True)
    resource_id: str
    chunk_index: int
    text: str

class Embedding(SQLModel, table=True):
    id: str = Field(default_factory=gen_id, primary_key=True)
    chunk_id: str
    vector: str  # JSON of floats

class Question(SQLModel, table=True):
    id: str = Field(default_factory=gen_id, primary_key=True)
    plan_id: str
    topic: str
    stem: str
    choices: Optional[str] = None
    answer_index: Optional[int] = None
    explanation: Optional[str] = None
