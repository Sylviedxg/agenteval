import uuid
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class Trace(Base, TimestampMixin):
    __tablename__ = "traces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id"),
        nullable=False
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    raw_trace: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    experiment = relationship("Experiment", back_populates="traces")
    case = relationship("Case", back_populates="traces")
    node_results = relationship("NodeResult", back_populates="trace")


class NodeResult(Base, TimestampMixin):
    __tablename__ = "node_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("traces.id"),
        nullable=False
    )
    node_name: Mapped[str] = mapped_column(String(100), nullable=False)
    node_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metric_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    auto_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    manual_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    node_input: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    node_output: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    trace = relationship("Trace", back_populates="node_results")
