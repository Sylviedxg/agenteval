import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class ConfigSnapshot(Base, TimestampMixin):
    __tablename__ = "config_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False
    )
    snapshot_name: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt_versions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    model_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tools_version: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    skills_version: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    memory_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    diff_from_previous: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    product = relationship("Product", back_populates="config_snapshots")
    experiments = relationship("Experiment", back_populates="config_snapshot")


class EvalPlan(Base, TimestampMixin):
    __tablename__ = "eval_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metric_ids: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)
    node_metric_mapping: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    experiments = relationship("Experiment", back_populates="eval_plan")


class Experiment(Base, TimestampMixin):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id"),
        nullable=False
    )
    config_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("config_snapshots.id"),
        nullable=False
    )
    eval_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("eval_plans.id"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    completed_cases: Mapped[int] = mapped_column(Integer, default=0)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    result_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    product = relationship("Product", back_populates="experiments")
    dataset = relationship("Dataset", back_populates="experiments")
    config_snapshot = relationship("ConfigSnapshot", back_populates="experiments")
    eval_plan = relationship("EvalPlan", back_populates="experiments")
    traces = relationship("Trace", back_populates="experiment")
