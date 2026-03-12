import uuid
from typing import Optional
from sqlalchemy import String, Text, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class MetricDefinition(Base, TimestampMixin):
    __tablename__ = "metric_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metric_type: Mapped[str] = mapped_column(String(20), nullable=False)
    scoring_method: Mapped[str] = mapped_column(String(20), nullable=False)
    score_range_min: Mapped[float] = mapped_column(Float, default=0)
    score_range_max: Mapped[float] = mapped_column(Float, default=10)
    evaluation_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    node_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
