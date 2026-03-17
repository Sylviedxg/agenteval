"""
评测节点模型 - 基于 tanqi_eval_v2.xlsx 设计
33个节点，三层架构，双轨评分（客观70% + 主观30%）
"""
import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base
from app.models.base import TimestampMixin


class NodeLayer(str, enum.Enum):
    """节点层级"""
    L0_MAIN_AGENT = "L0_MainAgent"  # MainAgent内部节点
    L1_SINGLE = "L1_Single"          # 单体层（CardAgent节点）
    L2_COLLAB = "L2_Collab"          # 协作层（层间交接）
    L3_SYSTEM = "L3_System"          # 系统层（端到端）


class GateType(str, enum.Enum):
    """Gate类型"""
    GATE_0 = "Gate0"   # MainAgent LLM调用后
    GATE_A = "GateA"   # Layer0结束
    GATE_B = "GateB"   # Layer1结束
    GATE_C = "GateC"   # Layer2结束


class EvalNodeDefinition(Base, TimestampMixin):
    """
    评测节点定义 - 33个节点的元数据
    对应表格中的每一行
    """
    __tablename__ = "eval_node_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 基础信息
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 如 MainAgent, SearchCardAgent
    node_name: Mapped[str] = mapped_column(String(200), nullable=False)   # 如 LLM调用(意图理解+规划)
    node_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)  # 唯一编码
    layer_tag: Mapped[str] = mapped_column(String(50), nullable=False)    # Layer0/1/2 或 Layer0→1
    eval_layer: Mapped[str] = mapped_column(String(50), nullable=False)   # L0 MainAgent / L1 单体 / L2 协作 / L3 系统
    
    # 客观指标1
    obj_metric_1_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    obj_metric_1_source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # 如 Langfuse duration(ms)
    
    # 客观指标2
    obj_metric_2_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    obj_metric_2_source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # 客观指标3
    obj_metric_3_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    obj_metric_3_source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # 主观指标1
    subj_metric_1_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subj_metric_1_method: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # 如 LLM初评+人工复核（1-5分）
    
    # 主观指标2
    subj_metric_2_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subj_metric_2_method: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # 评分公式
    obj_score_formula: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # 客观得分计算公式
    subj_score_formula: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 主观得分计算公式
    final_score_formula: Mapped[str] = mapped_column(String(100), default="客观*0.7 + 主观*0.3")
    
    # 归属和权重
    belongs_to: Mapped[str] = mapped_column(String(100), nullable=False)  # 归属Agent
    layer_weight: Mapped[str] = mapped_column(String(100), nullable=False)  # 如 Layer0权重30%
    node_weight_rule: Mapped[str] = mapped_column(String(200), nullable=False)  # 如 节点均分 / Gate节点×1.5
    
    # Gate相关
    is_gate: Mapped[bool] = mapped_column(Boolean, default=False)
    gate_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Gate0/A/B/C
    gate_condition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # Gate通过条件
    
    # 备注
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class GateDefinition(Base, TimestampMixin):
    """
    Gate质量关口定义
    嵌在层间，执行过程中的质量关口
    """
    __tablename__ = "gate_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    gate_type: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)  # Gate0/A/B/C
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Gate位置
    trigger_point: Mapped[str] = mapped_column(String(200), nullable=False)  # 触发点描述
    source_layer: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 来源层
    target_layer: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 目标层
    
    # 通过条件
    pass_conditions: Mapped[dict] = mapped_column(JSON, nullable=False)  # 通过条件配置
    
    # 失败处理
    on_fail_action: Mapped[str] = mapped_column(String(100), nullable=False)  # 失败时动作：retry/rollback/manual_review
    retry_limit: Mapped[int] = mapped_column(Integer, default=3)
    
    # 关联的节点
    related_node_codes: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class NodeScoreResult(Base, TimestampMixin):
    """
    节点评分结果 - 单次评测中每个节点的得分
    """
    __tablename__ = "node_score_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 关联
    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("traces.id"),
        nullable=False
    )
    node_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("eval_node_definitions.id"),
        nullable=False
    )
    
    # 客观指标原始值
    obj_metric_1_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    obj_metric_2_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    obj_metric_3_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    obj_raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Langfuse原始数据
    
    # 客观得分（归一化后）
    obj_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1
    
    # 主观指标
    subj_metric_1_llm_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # LLM初评 1-5
    subj_metric_1_human_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 人工复核 1-5
    subj_metric_1_final: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 最终分
    
    subj_metric_2_llm_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    subj_metric_2_human_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    subj_metric_2_final: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # 主观得分（归一化后）
    subj_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1
    
    # 最终得分
    final_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 客观*0.7 + 主观*0.3
    
    # 是否需要人工复核
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    human_review_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    human_reviewer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 关联
    node_definition: Mapped["EvalNodeDefinition"] = relationship("EvalNodeDefinition")


class GateCheckResult(Base, TimestampMixin):
    """
    Gate检查结果 - 单次评测中每个Gate的检查结果
    """
    __tablename__ = "gate_check_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 关联
    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("traces.id"),
        nullable=False
    )
    gate_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gate_definitions.id"),
        nullable=False
    )
    
    # 检查结果
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    check_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 各条件检查详情
    
    # 失败处理
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    action_taken: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rollback_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 回溯到哪个节点
    
    # 时间戳
    checked_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 关联
    gate_definition: Mapped["GateDefinition"] = relationship("GateDefinition")


class LayerAggregateScore(Base, TimestampMixin):
    """
    层级聚合得分 - 单次评测中每层的聚合得分
    """
    __tablename__ = "layer_aggregate_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 关联
    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("traces.id"),
        nullable=False
    )
    
    # 层级
    layer: Mapped[str] = mapped_column(String(50), nullable=False)  # Layer0/Layer1/Layer2
    
    # 各节点得分明细
    node_scores: Mapped[dict] = mapped_column(JSON, nullable=False)  # {node_code: {score, weight}}
    
    # 聚合得分
    aggregate_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # 层级权重
    layer_weight: Mapped[float] = mapped_column(Float, nullable=False)  # 0.3/0.3/0.4
    
    # 加权后得分（贡献到总分）
    weighted_score: Mapped[float] = mapped_column(Float, nullable=False)


class InvestigationScore(Base, TimestampMixin):
    """
    Investigation总分 - 单次评测的最终得分
    """
    __tablename__ = "investigation_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 关联
    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("traces.id"),
        nullable=False,
        unique=True
    )
    
    # 各层得分
    layer0_score: Mapped[float] = mapped_column(Float, nullable=False)
    layer1_score: Mapped[float] = mapped_column(Float, nullable=False)
    layer2_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # 总分 = Layer0*0.3 + Layer1*0.3 + Layer2*0.4
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Gate通过情况
    gates_passed: Mapped[dict] = mapped_column(JSON, nullable=False)  # {Gate0: true, GateA: true, ...}
    all_gates_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    
    # 质量等级
    quality_level: Mapped[str] = mapped_column(String(20), nullable=False)  # A/B/C/D/F
    
    # 问题摘要
    issues_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 人工复核状态
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    human_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
