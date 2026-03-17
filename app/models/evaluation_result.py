"""
评测结果存储模型 - 存储 Langfuse Trace 的评测结果
"""
import uuid
from typing import Optional
from sqlalchemy import String, Text, Float, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class EvaluationResult(Base, TimestampMixin):
    """
    评测结果 - 存储单次 Langfuse Trace 的完整评测结果
    """
    __tablename__ = "evaluation_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Langfuse 信息
    langfuse_trace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    trace_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Trace 元数据
    trace_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    trace_timestamp: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    trace_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trace_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    observations_count: Mapped[int] = mapped_column(default=0)
    
    # 各节点得分
    node_scores: Mapped[dict] = mapped_column(JSON, nullable=False)  # {node_code: {obj_score, subj_score, final_score, ...}}
    
    # 层级得分
    layer0_score: Mapped[float] = mapped_column(Float, nullable=False)
    layer0_nodes: Mapped[int] = mapped_column(default=0)
    layer1_score: Mapped[float] = mapped_column(Float, nullable=False)
    layer1_nodes: Mapped[int] = mapped_column(default=0)
    layer2_score: Mapped[float] = mapped_column(Float, nullable=False)
    layer2_nodes: Mapped[int] = mapped_column(default=0)
    
    # 总分
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    quality_level: Mapped[str] = mapped_column(String(10), nullable=False)  # A/B/C/D/F
    
    # Gate 检查
    gates_passed: Mapped[dict] = mapped_column(JSON, nullable=False)  # {Gate0: true, ...}
    all_gates_passed: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 原始数据摘要
    raw_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 备注
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
