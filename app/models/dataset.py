import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class Dataset(Base, TimestampMixin):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    case_count: Mapped[int] = mapped_column(Integer, default=0)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # excel_import, manual, etc.
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 存储节点定义、场景等

    cases = relationship("Case", back_populates="dataset")
    experiments = relationship("Experiment", back_populates="dataset")


class Case(Base, TimestampMixin):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id"),
        nullable=False
    )
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # 用例名称
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    input_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 改为可选
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 结构化输入
    expected_agent_path: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    expected_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 期望输出
    golden_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 存储expected_scores等
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    dataset = relationship("Dataset", back_populates="cases")
    traces = relationship("Trace", back_populates="case")
