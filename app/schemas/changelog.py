from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ChangelogCreate(BaseModel):
    product_id: Optional[UUID] = None
    experiment_id: Optional[UUID] = None
    change_type: str
    title: str
    description: Optional[str] = None
    before_snapshot_id: Optional[UUID] = None
    after_snapshot_id: Optional[UUID] = None
    impact_assessment: Optional[str] = None


class ChangelogResponse(BaseModel):
    id: UUID
    product_id: Optional[UUID] = None
    experiment_id: Optional[UUID] = None
    change_type: str
    title: str
    description: Optional[str] = None
    before_snapshot_id: Optional[UUID] = None
    after_snapshot_id: Optional[UUID] = None
    impact_assessment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
