from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== 指标分类 ====================

class MetricCategoryBase(BaseModel):
    name: str = Field(..., description="分类名称")
    code: str = Field(..., description="分类编码")
    level: str = Field(..., description="层级: system/collaboration/agent")
    description: Optional[str] = Field(None, description="描述")
    parent_id: Optional[UUID] = Field(None, description="父分类ID")
    sort_order: int = Field(0, description="排序")


class MetricCategoryCreate(MetricCategoryBase):
    pass


class MetricCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class MetricCategoryResponse(MetricCategoryBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MetricCategoryWithMetrics(MetricCategoryResponse):
    metrics: List["MetricDefinitionResponse"] = []


# ==================== 指标定义 ====================

class MetricDefinitionBase(BaseModel):
    name: str = Field(..., description="指标名称")
    code: str = Field(..., description="指标编码")
    description: Optional[str] = Field(None, description="描述")
    category_id: Optional[UUID] = Field(None, description="分类ID")
    metric_type: str = Field(..., description="指标类型: process/result")
    scoring_method: str = Field(..., description="评分方式: auto/manual/hybrid")
    data_type: str = Field("number", description="数据类型: number/percentage/duration/boolean/score")
    score_range_min: float = Field(0, description="评分下限")
    score_range_max: float = Field(10, description="评分上限")
    unit: Optional[str] = Field(None, description="单位")
    evaluation_criteria: Optional[str] = Field(None, description="评估标准")
    applicable_node_types: Optional[List[str]] = Field(None, description="适用节点类型")
    collection_method: str = Field("manual", description="采集方式: langfuse/api/manual/computed")
    collection_config: Optional[dict] = Field(None, description="采集配置")
    aggregation_method: str = Field("avg", description="聚合方式: avg/sum/max/min/last/count")
    weight: float = Field(1.0, description="权重")
    thresholds: Optional[dict] = Field(None, description="阈值配置")
    sort_order: int = Field(0, description="排序")


class MetricDefinitionCreate(MetricDefinitionBase):
    pass


class MetricDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    metric_type: Optional[str] = None
    scoring_method: Optional[str] = None
    data_type: Optional[str] = None
    score_range_min: Optional[float] = None
    score_range_max: Optional[float] = None
    unit: Optional[str] = None
    evaluation_criteria: Optional[str] = None
    applicable_node_types: Optional[List[str]] = None
    collection_method: Optional[str] = None
    collection_config: Optional[dict] = None
    aggregation_method: Optional[str] = None
    weight: Optional[float] = None
    thresholds: Optional[dict] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class MetricDefinitionResponse(MetricDefinitionBase):
    id: UUID
    is_active: bool
    is_builtin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 里程碑检查点 ====================

class MilestoneBase(BaseModel):
    name: str = Field(..., description="里程碑名称")
    code: str = Field(..., description="里程碑编码")
    description: Optional[str] = Field(None, description="描述")
    checkpoint_type: str = Field(..., description="检查点类型: entry/process/output/exit")
    applicable_node_types: Optional[List[str]] = Field(None, description="适用节点类型")
    check_conditions: Optional[dict] = Field(None, description="检查条件")
    related_metrics: Optional[List[str]] = Field(None, description="关联指标编码")
    sort_order: int = Field(0, description="排序")


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    checkpoint_type: Optional[str] = None
    applicable_node_types: Optional[List[str]] = None
    check_conditions: Optional[dict] = None
    related_metrics: Optional[List[str]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class MilestoneResponse(MilestoneBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Agent 类型 ====================

class AgentTypeBase(BaseModel):
    name: str = Field(..., description="Agent类型名称")
    code: str = Field(..., description="Agent类型编码")
    description: Optional[str] = Field(None, description="描述")
    layer: str = Field(..., description="层级: layer_0/layer_1/layer_2/orchestrator")
    card_type: Optional[str] = Field(None, description="对应的CardType")
    class_name: Optional[str] = Field(None, description="Agent类名")
    execution_flow: Optional[dict] = Field(None, description="执行链路")
    io_definition: Optional[dict] = Field(None, description="输入输出定义")
    available_tools: Optional[List[str]] = Field(None, description="可用工具列表")
    sort_order: int = Field(0, description="排序")


class AgentTypeCreate(AgentTypeBase):
    pass


class AgentTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    layer: Optional[str] = None
    card_type: Optional[str] = None
    class_name: Optional[str] = None
    execution_flow: Optional[dict] = None
    io_definition: Optional[dict] = None
    available_tools: Optional[List[str]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class AgentTypeResponse(AgentTypeBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Agent 指标映射 ====================

class AgentMetricMappingBase(BaseModel):
    agent_type_id: UUID = Field(..., description="Agent类型ID")
    metric_id: UUID = Field(..., description="指标ID")
    weight_override: Optional[float] = Field(None, description="权重覆盖")
    thresholds_override: Optional[dict] = Field(None, description="阈值覆盖")
    is_core: bool = Field(False, description="是否核心指标")
    collection_config_override: Optional[dict] = Field(None, description="采集配置覆盖")


class AgentMetricMappingCreate(AgentMetricMappingBase):
    pass


class AgentMetricMappingResponse(AgentMetricMappingBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    metric: Optional[MetricDefinitionResponse] = None

    class Config:
        from_attributes = True


class AgentTypeWithMetrics(AgentTypeResponse):
    """带指标映射的Agent类型"""
    metric_mappings: List[AgentMetricMappingResponse] = []
    core_metrics: List[MetricDefinitionResponse] = []  # 核心指标列表


# ==================== 指标体系概览 ====================

class MetricSystemOverview(BaseModel):
    """三层指标体系概览"""
    system_level: List[MetricCategoryWithMetrics] = Field([], description="系统层指标")
    collaboration_level: List[MetricCategoryWithMetrics] = Field([], description="协作层指标")
    agent_level: List[MetricCategoryWithMetrics] = Field([], description="单体层指标")
    milestones: List[MilestoneResponse] = Field([], description="里程碑检查点")
    total_metrics: int = Field(0, description="指标总数")
    total_milestones: int = Field(0, description="里程碑总数")


class AgentTypeOverview(BaseModel):
    """Agent类型概览"""
    layer_0: List[AgentTypeWithMetrics] = Field([], description="Layer 0 数据采集")
    layer_1: List[AgentTypeWithMetrics] = Field([], description="Layer 1 数据分析")
    layer_2: List[AgentTypeWithMetrics] = Field([], description="Layer 2 报告生成")
    orchestrator: List[AgentTypeWithMetrics] = Field([], description="编排层")
    total_agent_types: int = Field(0, description="Agent类型总数")


# 解决循环引用
MetricCategoryWithMetrics.model_rebuild()
AgentTypeWithMetrics.model_rebuild()
