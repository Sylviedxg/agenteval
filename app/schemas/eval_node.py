"""
评测节点 Schema - 基于 tanqi_eval_v2.xlsx 设计
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== 节点定义 ====================

class EvalNodeDefinitionBase(BaseModel):
    agent_name: str = Field(..., description="Agent名称")
    node_name: str = Field(..., description="节点名称")
    node_code: str = Field(..., description="节点编码")
    layer_tag: str = Field(..., description="层级标签")
    eval_layer: str = Field(..., description="评测层级")
    
    obj_metric_1_name: Optional[str] = None
    obj_metric_1_source: Optional[str] = None
    obj_metric_2_name: Optional[str] = None
    obj_metric_2_source: Optional[str] = None
    obj_metric_3_name: Optional[str] = None
    obj_metric_3_source: Optional[str] = None
    
    subj_metric_1_name: Optional[str] = None
    subj_metric_1_method: Optional[str] = None
    subj_metric_2_name: Optional[str] = None
    subj_metric_2_method: Optional[str] = None
    
    obj_score_formula: Optional[str] = None
    subj_score_formula: Optional[str] = None
    final_score_formula: str = "客观*0.7 + 主观*0.3"
    
    belongs_to: str = Field(..., description="归属Agent")
    layer_weight: str = Field(..., description="层级权重")
    node_weight_rule: str = Field(..., description="节点权重规则")
    
    is_gate: bool = False
    gate_type: Optional[str] = None
    gate_condition: Optional[str] = None
    remark: Optional[str] = None
    sort_order: int = 0


class EvalNodeDefinitionCreate(EvalNodeDefinitionBase):
    pass


class EvalNodeDefinitionResponse(EvalNodeDefinitionBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Gate定义 ====================

class GateDefinitionBase(BaseModel):
    gate_type: str = Field(..., description="Gate类型")
    name: str = Field(..., description="Gate名称")
    description: Optional[str] = None
    trigger_point: str = Field(..., description="触发点")
    source_layer: Optional[str] = None
    target_layer: Optional[str] = None
    pass_conditions: dict = Field(..., description="通过条件")
    on_fail_action: str = Field(..., description="失败动作")
    retry_limit: int = 3
    related_node_codes: Optional[List[str]] = None
    sort_order: int = 0


class GateDefinitionCreate(GateDefinitionBase):
    pass


class GateDefinitionResponse(GateDefinitionBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 节点评分结果 ====================

class NodeScoreResultBase(BaseModel):
    trace_id: UUID
    node_definition_id: UUID
    
    obj_metric_1_value: Optional[float] = None
    obj_metric_2_value: Optional[float] = None
    obj_metric_3_value: Optional[float] = None
    obj_raw_data: Optional[dict] = None
    obj_score: Optional[float] = None
    
    subj_metric_1_llm_score: Optional[float] = None
    subj_metric_1_human_score: Optional[float] = None
    subj_metric_1_final: Optional[float] = None
    subj_metric_2_llm_score: Optional[float] = None
    subj_metric_2_human_score: Optional[float] = None
    subj_metric_2_final: Optional[float] = None
    subj_score: Optional[float] = None
    
    final_score: Optional[float] = None
    needs_human_review: bool = False
    human_review_reason: Optional[str] = None


class NodeScoreResultCreate(NodeScoreResultBase):
    pass


class NodeScoreResultUpdate(BaseModel):
    subj_metric_1_human_score: Optional[float] = None
    subj_metric_2_human_score: Optional[float] = None
    human_reviewed: bool = False
    human_reviewer: Optional[str] = None


class NodeScoreResultResponse(NodeScoreResultBase):
    id: UUID
    human_reviewed: bool
    human_reviewer: Optional[str]
    created_at: datetime
    updated_at: datetime
    node_definition: Optional[EvalNodeDefinitionResponse] = None

    class Config:
        from_attributes = True


# ==================== Gate检查结果 ====================

class GateCheckResultBase(BaseModel):
    trace_id: UUID
    gate_definition_id: UUID
    passed: bool
    check_details: Optional[dict] = None
    retry_count: int = 0
    action_taken: Optional[str] = None
    rollback_to: Optional[str] = None


class GateCheckResultCreate(GateCheckResultBase):
    pass


class GateCheckResultResponse(GateCheckResultBase):
    id: UUID
    checked_at: Optional[str]
    created_at: datetime
    updated_at: datetime
    gate_definition: Optional[GateDefinitionResponse] = None

    class Config:
        from_attributes = True


# ==================== 层级聚合得分 ====================

class LayerAggregateScoreBase(BaseModel):
    trace_id: UUID
    layer: str
    node_scores: dict
    aggregate_score: float
    layer_weight: float
    weighted_score: float


class LayerAggregateScoreResponse(LayerAggregateScoreBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Investigation总分 ====================

class InvestigationScoreBase(BaseModel):
    trace_id: UUID
    layer0_score: float
    layer1_score: float
    layer2_score: float
    total_score: float
    gates_passed: dict
    all_gates_passed: bool
    quality_level: str
    issues_summary: Optional[dict] = None
    needs_human_review: bool = False


class InvestigationScoreResponse(InvestigationScoreBase):
    id: UUID
    human_reviewed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 评测概览 ====================

class EvalNodeOverview(BaseModel):
    """节点评测概览"""
    total_nodes: int = Field(0, description="总节点数")
    l0_nodes: List[EvalNodeDefinitionResponse] = Field([], description="L0 MainAgent节点")
    l1_nodes: List[EvalNodeDefinitionResponse] = Field([], description="L1 单体层节点")
    l2_nodes: List[EvalNodeDefinitionResponse] = Field([], description="L2 协作层节点")
    l3_nodes: List[EvalNodeDefinitionResponse] = Field([], description="L3 系统层节点")
    gates: List[GateDefinitionResponse] = Field([], description="Gate定义")


class TraceEvalResult(BaseModel):
    """单次Trace的完整评测结果"""
    trace_id: UUID
    investigation_score: Optional[InvestigationScoreResponse] = None
    layer_scores: List[LayerAggregateScoreResponse] = []
    node_scores: List[NodeScoreResultResponse] = []
    gate_results: List[GateCheckResultResponse] = []
    needs_human_review: bool = False
    human_review_nodes: List[str] = []  # 需要人工复核的节点code列表
