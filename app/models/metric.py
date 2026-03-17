import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class MetricCategory(Base, TimestampMixin):
    """指标分类 - 三层评测体系"""
    __tablename__ = "metric_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # system/collaboration/agent
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metric_categories.id"),
        nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关联
    metrics: Mapped[List["MetricDefinition"]] = relationship(
        "MetricDefinition",
        back_populates="category",
        lazy="selectin"
    )


class MetricDefinition(Base, TimestampMixin):
    """指标定义"""
    __tablename__ = "metric_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metric_categories.id"),
        nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 指标类型: process(过程指标) / result(结果指标)
    metric_type: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # 评分方式: auto(自动) / manual(人工) / hybrid(混合)
    scoring_method: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # 数据类型: number(数值) / percentage(百分比) / duration(时长) / boolean(布尔) / score(评分)
    data_type: Mapped[str] = mapped_column(String(20), default="number")
    
    # 评分范围
    score_range_min: Mapped[float] = mapped_column(Float, default=0)
    score_range_max: Mapped[float] = mapped_column(Float, default=10)
    
    # 单位
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # 评估标准 (JSON格式，支持复杂规则)
    evaluation_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 适用的节点类型 (JSON数组): ["main_agent", "search_card", "report_card", ...]
    applicable_node_types: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 采集方式: langfuse / api / manual / computed
    collection_method: Mapped[str] = mapped_column(String(20), default="manual")
    
    # 采集配置 (JSON格式，如 Langfuse span 名称、API 路径等)
    collection_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 聚合方式: avg / sum / max / min / last / count
    aggregation_method: Mapped[str] = mapped_column(String(20), default="avg")
    
    # 权重 (用于综合评分计算)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    
    # 阈值配置 (JSON格式): {"good": 0.8, "warning": 0.6, "bad": 0.4}
    thresholds: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)  # 内置指标不可删除

    # 关联
    category: Mapped[Optional["MetricCategory"]] = relationship(
        "MetricCategory",
        back_populates="metrics"
    )


class AgentType(Base, TimestampMixin):
    """Agent 类型定义 - 用于建立指标与 Agent 类型的映射"""
    __tablename__ = "agent_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Agent 层级: layer_0(数据采集) / layer_1(数据分析) / layer_2(报告生成) / orchestrator(编排)
    layer: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # 对应的 CardType (与 TanQi 代码中的 CardType 枚举对应)
    card_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Agent 类名 (如 SearchCardAgent, ChartCardAgent)
    class_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 执行链路描述 (JSON格式)
    execution_flow: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 输入输出定义 (JSON格式)
    io_definition: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 可用工具列表 (JSON数组)
    available_tools: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关联的指标
    metric_mappings: Mapped[List["AgentMetricMapping"]] = relationship(
        "AgentMetricMapping",
        back_populates="agent_type",
        lazy="selectin"
    )


class AgentMetricMapping(Base, TimestampMixin):
    """Agent 类型与指标的映射关系"""
    __tablename__ = "agent_metric_mappings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    agent_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_types.id"),
        nullable=False
    )
    metric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metric_definitions.id"),
        nullable=False
    )
    
    # 该指标在此 Agent 类型中的权重 (可覆盖指标默认权重)
    weight_override: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # 该指标在此 Agent 类型中的阈值 (可覆盖指标默认阈值)
    thresholds_override: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 是否为该 Agent 类型的核心指标
    is_core: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 采集配置覆盖 (针对特定 Agent 类型的采集配置)
    collection_config_override: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 关联
    agent_type: Mapped["AgentType"] = relationship(
        "AgentType",
        back_populates="metric_mappings"
    )
    metric: Mapped["MetricDefinition"] = relationship("MetricDefinition")


class Milestone(Base, TimestampMixin):
    """里程碑检查点 - 用于评测关键节点"""
    __tablename__ = "milestones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 检查点类型: entry(入口) / process(过程) / output(输出) / exit(出口)
    checkpoint_type: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # 适用的节点类型
    applicable_node_types: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 检查条件 (JSON格式)
    check_conditions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 关联的指标 (JSON数组): ["metric_code_1", "metric_code_2"]
    related_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
