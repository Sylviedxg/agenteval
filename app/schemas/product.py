from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    config: Optional[dict[str, Any]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[dict[str, Any]] = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    version: str
    is_active: bool
    config: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
