from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class BadCaseCreate(BaseModel):
    trace_id: Optional[UUID] = None
    case_id: Optional[UUID] = None
    experiment_id: Optional[UUID] = None
    severity: str = "minor"
    problem_node: Optional[str] = None
    problem_type: Optional[str] = None
    description: Optional[str] = None
    root_cause: Optional[str] = None
    fix_suggestion: Optional[str] = None


class BadCaseUpdate(BaseModel):
    severity: Optional[str] = None
    problem_node: Optional[str] = None
    problem_type: Optional[str] = None
    description: Optional[str] = None
    root_cause: Optional[str] = None
    fix_suggestion: Optional[str] = None
    status: Optional[str] = None


class BadCaseResponse(BaseModel):
    id: UUID
    trace_id: Optional[UUID] = None
    case_id: Optional[UUID] = None
    experiment_id: Optional[UUID] = None
    severity: str
    problem_node: Optional[str] = None
    problem_type: Optional[str] = None
    description: Optional[str] = None
    root_cause: Optional[str] = None
    fix_suggestion: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
