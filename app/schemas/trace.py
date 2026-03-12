from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TraceCreate(BaseModel):
    experiment_id: UUID
    case_id: UUID
    status: str = "pending"
    raw_trace: Optional[dict[str, Any]] = None
    total_tokens: Optional[int] = None
    total_latency_ms: Optional[int] = None


class TraceResponse(BaseModel):
    id: UUID
    experiment_id: UUID
    case_id: UUID
    status: str
    raw_trace: Optional[dict[str, Any]] = None
    total_tokens: Optional[int] = None
    total_latency_ms: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
