from datetime import datetime
from typing import Optional, Any, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"


class DatasetResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    version: str
    case_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvalPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    metric_ids: List[str] = []
    node_metric_mapping: dict[str, Any] = {}


class EvalPlanResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    metric_ids: Optional[List[str]] = None
    node_metric_mapping: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConfigSnapshotCreate(BaseModel):
    product_id: UUID
    snapshot_name: str
    prompt_versions: Optional[dict[str, Any]] = None
    llm_config: Optional[dict[str, Any]] = None
    tools_version: Optional[dict[str, Any]] = None


class ConfigSnapshotResponse(BaseModel):
    id: UUID
    product_id: UUID
    snapshot_name: str
    prompt_versions: Optional[dict[str, Any]] = None
    llm_config: Optional[dict[str, Any]] = None
    tools_version: Optional[dict[str, Any]] = None
    skills_version: Optional[dict[str, Any]] = None
    memory_config: Optional[dict[str, Any]] = None
    diff_from_previous: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentCreate(BaseModel):
    name: str
    product_id: UUID
    dataset_id: UUID
    config_snapshot_id: Optional[UUID] = None
    eval_plan_id: Optional[UUID] = None


class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    total_cases: Optional[int] = None
    completed_cases: Optional[int] = None
    overall_score: Optional[float] = None
    result_summary: Optional[dict[str, Any]] = None


class ExperimentResponse(BaseModel):
    id: UUID
    name: str
    product_id: UUID
    dataset_id: UUID
    config_snapshot_id: Optional[UUID] = None
    eval_plan_id: Optional[UUID] = None
    status: str
    total_cases: int
    completed_cases: int
    overall_score: Optional[float] = None
    result_summary: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
