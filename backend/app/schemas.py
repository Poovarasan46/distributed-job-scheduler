from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field

# --- Queue Schemas ---
class QueueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    priority: int = Field(default=0)
    concurrency_limit: int = Field(default=10, gt=0)

class QueueResponse(QueueCreate):
    id: UUID
    project_id: UUID
    is_paused: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Job Schemas ---
class JobCreate(BaseModel):
    payload: Dict[str, Any]
    scheduled_at: Optional[datetime] = None
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_policy: str = Field(default="exponential", pattern="^(fixed|linear|exponential)$")

class JobResponse(BaseModel):
    id: UUID
    queue_id: UUID
    status: str
    payload: Dict[str, Any]
    scheduled_at: datetime
    max_retries: int
    retry_count: int
    retry_policy: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True