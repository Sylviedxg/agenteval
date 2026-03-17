from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.models.metric import MetricCategory, MetricDefinition, Milestone, AgentType, AgentMetricMapping
from app.schemas.metric import (
    MetricCategoryCreate, MetricCategoryUpdate, MetricCategoryResponse, MetricCategoryWithMetrics,
    MetricDefinitionCreate, MetricDefinitionUpdate, MetricDefinitionResponse,
    MilestoneCreate, MilestoneUpdate, MilestoneResponse,
    MetricSystemOverview,
    AgentTypeCreate, AgentTypeUpdate, AgentTypeResponse, AgentTypeWithMetrics,
    AgentMetricMappingCreate, AgentMetricMappingResponse,
    AgentTypeOverview
)

router = APIRouter(prefix="/metrics", tags=["指标库"])


# ==================== 指标分类 ====================

@router.get("/categories", response_model=List[MetricCategoryResponse])
async def list_categories(
    level: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取指标分类列表"""
    query = select(MetricCategory).where(MetricCategory.is_active == True)
    if level:
        query = query.where(MetricCategory.level == level)
    query = query.order_by(MetricCategory.sort_order, MetricCategory.created_at)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/categories", response_model=MetricCategoryResponse)
async def create_category(
    data: MetricCategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建指标分类"""
    category = MetricCategory(**data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=MetricCategoryResponse)
async def update_category(
    category_id: UUID,
    data: MetricCategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新指标分类"""
    result = await db.execute(
        select(MetricCategory).where(MetricCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """删除指标分类"""
    result = await db.execute(
        select(MetricCategory).where(MetricCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    category.is_active = False
    await db.commit()
    return {"success": True}


# ==================== 指标定义 ====================

@router.get("/definitions", response_model=List[MetricDefinitionResponse])
async def list_definitions(
    category_id: Optional[UUID] = None,
    metric_type: Optional[str] = None,
    scoring_method: Optional[str] = None,
    collection_method: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取指标定义列表"""
    query = select(MetricDefinition).where(MetricDefinition.is_active == True)
    
    if category_id:
        query = query.where(MetricDefinition.category_id == category_id)
    if metric_type:
        query = query.where(MetricDefinition.metric_type == metric_type)
    if scoring_method:
        query = query.where(MetricDefinition.scoring_method == scoring_method)
    if collection_method:
        query = query.where(MetricDefinition.collection_method == collection_method)
    
    query = query.order_by(MetricDefinition.sort_order, MetricDefinition.created_at)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/definitions/{definition_id}", response_model=MetricDefinitionResponse)
async def get_definition(
    definition_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取指标定义详情"""
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.id == definition_id)
    )
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(status_code=404, detail="指标不存在")
    return definition


@router.post("/definitions", response_model=MetricDefinitionResponse)
async def create_definition(
    data: MetricDefinitionCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建指标定义"""
    definition = MetricDefinition(**data.model_dump())
    db.add(definition)
    await db.commit()
    await db.refresh(definition)
    return definition


@router.put("/definitions/{definition_id}", response_model=MetricDefinitionResponse)
async def update_definition(
    definition_id: UUID,
    data: MetricDefinitionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新指标定义"""
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.id == definition_id)
    )
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(status_code=404, detail="指标不存在")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(definition, key, value)
    
    await db.commit()
    await db.refresh(definition)
    return definition


@router.delete("/definitions/{definition_id}")
async def delete_definition(
    definition_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """删除指标定义"""
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.id == definition_id)
    )
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(status_code=404, detail="指标不存在")
    
    if definition.is_builtin:
        raise HTTPException(status_code=400, detail="内置指标不可删除")
    
    definition.is_active = False
    await db.commit()
    return {"success": True}


# ==================== 里程碑检查点 ====================

@router.get("/milestones", response_model=List[MilestoneResponse])
async def list_milestones(
    checkpoint_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取里程碑列表"""
    query = select(Milestone).where(Milestone.is_active == True)
    if checkpoint_type:
        query = query.where(Milestone.checkpoint_type == checkpoint_type)
    query = query.order_by(Milestone.sort_order, Milestone.created_at)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/milestones", response_model=MilestoneResponse)
async def create_milestone(
    data: MilestoneCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建里程碑"""
    milestone = Milestone(**data.model_dump())
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    return milestone


@router.put("/milestones/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    milestone_id: UUID,
    data: MilestoneUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新里程碑"""
    result = await db.execute(
        select(Milestone).where(Milestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(milestone, key, value)
    
    await db.commit()
    await db.refresh(milestone)
    return milestone


@router.delete("/milestones/{milestone_id}")
async def delete_milestone(
    milestone_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """删除里程碑"""
    result = await db.execute(
        select(Milestone).where(Milestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    
    milestone.is_active = False
    await db.commit()
    return {"success": True}


# ==================== 指标体系概览 ====================

@router.get("/overview", response_model=MetricSystemOverview)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """获取三层指标体系概览"""
    # 获取所有分类和指标
    categories_result = await db.execute(
        select(MetricCategory)
        .where(MetricCategory.is_active == True)
        .order_by(MetricCategory.sort_order)
    )
    categories = categories_result.scalars().all()
    
    # 获取所有里程碑
    milestones_result = await db.execute(
        select(Milestone)
        .where(Milestone.is_active == True)
        .order_by(Milestone.sort_order)
    )
    milestones = milestones_result.scalars().all()
    
    # 获取所有指标
    definitions_result = await db.execute(
        select(MetricDefinition)
        .where(MetricDefinition.is_active == True)
    )
    definitions = definitions_result.scalars().all()
    
    # 按层级分组
    system_level = [c for c in categories if c.level == "system"]
    collaboration_level = [c for c in categories if c.level == "collaboration"]
    agent_level = [c for c in categories if c.level == "agent"]
    
    return MetricSystemOverview(
        system_level=system_level,
        collaboration_level=collaboration_level,
        agent_level=agent_level,
        milestones=milestones,
        total_metrics=len(definitions),
        total_milestones=len(milestones)
    )


# ==================== 初始化内置指标 ====================

@router.post("/init-builtin")
async def init_builtin_metrics(db: AsyncSession = Depends(get_db)):
    """初始化内置指标体系"""
    
    # 检查是否已初始化
    result = await db.execute(
        select(MetricCategory).where(MetricCategory.code == "system_performance")
    )
    if result.scalar_one_or_none():
        return {"message": "内置指标已存在", "initialized": False}
    
    # ========== 创建分类 ==========
    categories_data = [
        # 系统层
        {"name": "系统性能", "code": "system_performance", "level": "system", "sort_order": 1,
         "description": "整体系统性能指标，包括端到端延迟、吞吐量等"},
        {"name": "系统可靠性", "code": "system_reliability", "level": "system", "sort_order": 2,
         "description": "系统稳定性和可靠性指标"},
        {"name": "资源消耗", "code": "system_resource", "level": "system", "sort_order": 3,
         "description": "Token消耗、API调用次数等资源指标"},
        
        # 协作层
        {"name": "任务编排", "code": "collab_orchestration", "level": "collaboration", "sort_order": 1,
         "description": "MainAgent任务规划和编排质量"},
        {"name": "Agent协作", "code": "collab_coordination", "level": "collaboration", "sort_order": 2,
         "description": "多Agent协作效率和质量"},
        {"name": "信息传递", "code": "collab_communication", "level": "collaboration", "sort_order": 3,
         "description": "Agent间信息传递的准确性和完整性"},
        
        # 单体层
        {"name": "任务完成", "code": "agent_completion", "level": "agent", "sort_order": 1,
         "description": "单个Agent任务完成质量"},
        {"name": "工具使用", "code": "agent_tool_usage", "level": "agent", "sort_order": 2,
         "description": "工具调用的准确性和效率"},
        {"name": "输出质量", "code": "agent_output", "level": "agent", "sort_order": 3,
         "description": "Agent输出内容的质量"},
    ]
    
    category_map = {}
    for cat_data in categories_data:
        category = MetricCategory(**cat_data)
        db.add(category)
        await db.flush()
        category_map[cat_data["code"]] = category.id
    
    # ========== 创建指标 ==========
    metrics_data = [
        # 系统层 - 性能
        {"name": "端到端延迟", "code": "e2e_latency", "category_code": "system_performance",
         "metric_type": "process", "scoring_method": "auto", "data_type": "duration", "unit": "ms",
         "collection_method": "langfuse", "aggregation_method": "avg",
         "thresholds": {"good": 30000, "warning": 60000, "bad": 120000},
         "description": "从用户输入到最终输出的总耗时"},
        {"name": "首Token延迟(TTFT)", "code": "ttft", "category_code": "system_performance",
         "metric_type": "process", "scoring_method": "auto", "data_type": "duration", "unit": "ms",
         "collection_method": "langfuse", "aggregation_method": "avg",
         "thresholds": {"good": 2000, "warning": 5000, "bad": 10000},
         "description": "首个Token返回的延迟时间"},
        
        # 系统层 - 可靠性
        {"name": "任务成功率", "code": "task_success_rate", "category_code": "system_reliability",
         "metric_type": "result", "scoring_method": "auto", "data_type": "percentage", "unit": "%",
         "collection_method": "computed", "aggregation_method": "avg",
         "thresholds": {"good": 0.95, "warning": 0.8, "bad": 0.6},
         "description": "任务执行成功的比例"},
        {"name": "错误恢复率", "code": "error_recovery_rate", "category_code": "system_reliability",
         "metric_type": "process", "scoring_method": "auto", "data_type": "percentage", "unit": "%",
         "collection_method": "langfuse", "aggregation_method": "avg",
         "description": "遇到错误后成功恢复的比例"},
        
        # 系统层 - 资源
        {"name": "总Token消耗", "code": "total_tokens", "category_code": "system_resource",
         "metric_type": "process", "scoring_method": "auto", "data_type": "number", "unit": "tokens",
         "collection_method": "langfuse", "aggregation_method": "sum",
         "description": "整个任务消耗的Token总数"},
        {"name": "LLM调用次数", "code": "llm_calls", "category_code": "system_resource",
         "metric_type": "process", "scoring_method": "auto", "data_type": "number", "unit": "次",
         "collection_method": "langfuse", "aggregation_method": "sum",
         "description": "LLM API调用的总次数"},
        
        # 协作层 - 任务编排
        {"name": "任务规划合理性", "code": "plan_quality", "category_code": "collab_orchestration",
         "metric_type": "process", "scoring_method": "hybrid", "data_type": "score",
         "collection_method": "manual", "aggregation_method": "avg", "weight": 1.5,
         "thresholds": {"good": 8, "warning": 6, "bad": 4},
         "description": "任务分解和依赖关系的合理性"},
        {"name": "并行效率", "code": "parallel_efficiency", "category_code": "collab_orchestration",
         "metric_type": "process", "scoring_method": "auto", "data_type": "percentage", "unit": "%",
         "collection_method": "computed", "aggregation_method": "avg",
         "description": "并行任务的实际并行度"},
        
        # 协作层 - Agent协作
        {"name": "委派成功率", "code": "delegate_success_rate", "category_code": "collab_coordination",
         "metric_type": "process", "scoring_method": "auto", "data_type": "percentage", "unit": "%",
         "collection_method": "langfuse", "aggregation_method": "avg",
         "description": "任务委派给CardAgent后成功完成的比例"},
        {"name": "冒泡信息质量", "code": "bubble_quality", "category_code": "collab_coordination",
         "metric_type": "process", "scoring_method": "manual", "data_type": "score",
         "collection_method": "manual", "aggregation_method": "avg",
         "description": "CardAgent冒泡信息的有用性"},
        
        # 协作层 - 信息传递
        {"name": "上下文传递完整性", "code": "context_completeness", "category_code": "collab_communication",
         "metric_type": "process", "scoring_method": "manual", "data_type": "score",
         "collection_method": "manual", "aggregation_method": "avg",
         "description": "任务上下文传递的完整性"},
        
        # 单体层 - 任务完成
        {"name": "任务完成度", "code": "task_completion", "category_code": "agent_completion",
         "metric_type": "result", "scoring_method": "hybrid", "data_type": "score",
         "collection_method": "manual", "aggregation_method": "avg", "weight": 2.0,
         "thresholds": {"good": 8, "warning": 6, "bad": 4},
         "description": "Agent完成指定任务的程度"},
        {"name": "输出准确性", "code": "output_accuracy", "category_code": "agent_completion",
         "metric_type": "result", "scoring_method": "hybrid", "data_type": "score",
         "collection_method": "manual", "aggregation_method": "avg", "weight": 2.0,
         "description": "输出内容的准确性"},
        
        # 单体层 - 工具使用
        {"name": "工具选择准确率", "code": "tool_selection_accuracy", "category_code": "agent_tool_usage",
         "metric_type": "process", "scoring_method": "auto", "data_type": "percentage", "unit": "%",
         "collection_method": "langfuse", "aggregation_method": "avg",
         "description": "选择正确工具的比例"},
        {"name": "工具调用成功率", "code": "tool_call_success_rate", "category_code": "agent_tool_usage",
         "metric_type": "process", "scoring_method": "auto", "data_type": "percentage", "unit": "%",
         "collection_method": "langfuse", "aggregation_method": "avg",
         "description": "工具调用成功的比例"},
        {"name": "代码执行成功率", "code": "code_execution_success", "category_code": "agent_tool_usage",
         "metric_type": "process", "scoring_method": "auto", "data_type": "percentage", "unit": "%",
         "collection_method": "langfuse", "aggregation_method": "avg",
         "applicable_node_types": ["search_card", "chart_card", "report_card"],
         "description": "代码执行成功的比例"},
        
        # 单体层 - 输出质量
        {"name": "回答相关性", "code": "response_relevance", "category_code": "agent_output",
         "metric_type": "result", "scoring_method": "manual", "data_type": "score",
         "collection_method": "manual", "aggregation_method": "avg",
         "description": "回答与问题的相关程度"},
        {"name": "信息完整性", "code": "info_completeness", "category_code": "agent_output",
         "metric_type": "result", "scoring_method": "manual", "data_type": "score",
         "collection_method": "manual", "aggregation_method": "avg",
         "description": "输出信息的完整程度"},
        {"name": "可视化质量", "code": "visualization_quality", "category_code": "agent_output",
         "metric_type": "result", "scoring_method": "manual", "data_type": "score",
         "collection_method": "manual", "aggregation_method": "avg",
         "applicable_node_types": ["chart_card", "map_card", "network_card", "timeline_card"],
         "description": "图表/地图等可视化输出的质量"},
    ]
    
    for metric_data in metrics_data:
        category_code = metric_data.pop("category_code")
        metric_data["category_id"] = category_map.get(category_code)
        metric_data["is_builtin"] = True
        metric = MetricDefinition(**metric_data)
        db.add(metric)
    
    # ========== 创建里程碑 ==========
    milestones_data = [
        {"name": "请求接收", "code": "request_received", "checkpoint_type": "entry", "sort_order": 1,
         "description": "用户请求进入系统",
         "related_metrics": ["ttft"]},
        {"name": "任务规划完成", "code": "plan_completed", "checkpoint_type": "process", "sort_order": 2,
         "description": "MainAgent完成任务规划",
         "related_metrics": ["plan_quality", "parallel_efficiency"]},
        {"name": "数据采集完成", "code": "data_collection_done", "checkpoint_type": "process", "sort_order": 3,
         "description": "Layer 0 数据采集任务完成",
         "applicable_node_types": ["search_card", "company_card", "jingqi_card"],
         "related_metrics": ["delegate_success_rate", "tool_call_success_rate"]},
        {"name": "数据分析完成", "code": "data_analysis_done", "checkpoint_type": "process", "sort_order": 4,
         "description": "Layer 1 数据分析任务完成",
         "applicable_node_types": ["chart_card", "map_card", "network_card", "timeline_card"],
         "related_metrics": ["visualization_quality", "output_accuracy"]},
        {"name": "报告生成完成", "code": "report_generated", "checkpoint_type": "output", "sort_order": 5,
         "description": "Layer 2 报告生成完成",
         "applicable_node_types": ["report_card"],
         "related_metrics": ["task_completion", "info_completeness"]},
        {"name": "响应返回", "code": "response_sent", "checkpoint_type": "exit", "sort_order": 6,
         "description": "最终响应返回给用户",
         "related_metrics": ["e2e_latency", "task_success_rate"]},
    ]
    
    for milestone_data in milestones_data:
        milestone = Milestone(**milestone_data)
        db.add(milestone)
    
    await db.commit()
    
    return {
        "message": "内置指标初始化成功",
        "initialized": True,
        "categories": len(categories_data),
        "metrics": len(metrics_data),
        "milestones": len(milestones_data)
    }


# ==================== Agent 类型 ====================

@router.get("/agent-types", response_model=List[AgentTypeResponse])
async def list_agent_types(
    layer: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取 Agent 类型列表"""
    query = select(AgentType).where(AgentType.is_active == True)
    if layer:
        query = query.where(AgentType.layer == layer)
    query = query.order_by(AgentType.sort_order, AgentType.created_at)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/agent-types/{agent_type_id}", response_model=AgentTypeWithMetrics)
async def get_agent_type(
    agent_type_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取 Agent 类型详情（含指标映射）"""
    result = await db.execute(
        select(AgentType).where(AgentType.id == agent_type_id)
    )
    agent_type = result.scalar_one_or_none()
    if not agent_type:
        raise HTTPException(status_code=404, detail="Agent类型不存在")
    
    # 获取核心指标
    core_metrics = []
    for mapping in agent_type.metric_mappings:
        if mapping.is_core:
            core_metrics.append(mapping.metric)
    
    return AgentTypeWithMetrics(
        **{k: v for k, v in agent_type.__dict__.items() if not k.startswith('_')},
        metric_mappings=agent_type.metric_mappings,
        core_metrics=core_metrics
    )


@router.post("/agent-types", response_model=AgentTypeResponse)
async def create_agent_type(
    data: AgentTypeCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建 Agent 类型"""
    agent_type = AgentType(**data.model_dump())
    db.add(agent_type)
    await db.commit()
    await db.refresh(agent_type)
    return agent_type


@router.put("/agent-types/{agent_type_id}", response_model=AgentTypeResponse)
async def update_agent_type(
    agent_type_id: UUID,
    data: AgentTypeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新 Agent 类型"""
    result = await db.execute(
        select(AgentType).where(AgentType.id == agent_type_id)
    )
    agent_type = result.scalar_one_or_none()
    if not agent_type:
        raise HTTPException(status_code=404, detail="Agent类型不存在")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(agent_type, key, value)
    
    await db.commit()
    await db.refresh(agent_type)
    return agent_type


@router.delete("/agent-types/{agent_type_id}")
async def delete_agent_type(
    agent_type_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """删除 Agent 类型"""
    result = await db.execute(
        select(AgentType).where(AgentType.id == agent_type_id)
    )
    agent_type = result.scalar_one_or_none()
    if not agent_type:
        raise HTTPException(status_code=404, detail="Agent类型不存在")
    
    agent_type.is_active = False
    await db.commit()
    return {"success": True}


# ==================== Agent 指标映射 ====================

@router.post("/agent-types/{agent_type_id}/metrics", response_model=AgentMetricMappingResponse)
async def add_metric_to_agent_type(
    agent_type_id: UUID,
    data: AgentMetricMappingCreate,
    db: AsyncSession = Depends(get_db)
):
    """为 Agent 类型添加指标映射"""
    # 验证 Agent 类型存在
    result = await db.execute(
        select(AgentType).where(AgentType.id == agent_type_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent类型不存在")
    
    # 验证指标存在
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.id == data.metric_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="指标不存在")
    
    mapping = AgentMetricMapping(
        agent_type_id=agent_type_id,
        **data.model_dump(exclude={"agent_type_id"})
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.delete("/agent-types/{agent_type_id}/metrics/{mapping_id}")
async def remove_metric_from_agent_type(
    agent_type_id: UUID,
    mapping_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """移除 Agent 类型的指标映射"""
    result = await db.execute(
        select(AgentMetricMapping).where(
            and_(
                AgentMetricMapping.id == mapping_id,
                AgentMetricMapping.agent_type_id == agent_type_id
            )
        )
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=404, detail="映射不存在")
    
    await db.delete(mapping)
    await db.commit()
    return {"success": True}


# ==================== Agent 类型概览 ====================

@router.get("/agent-types-overview", response_model=AgentTypeOverview)
async def get_agent_types_overview(db: AsyncSession = Depends(get_db)):
    """获取 Agent 类型概览（按层级分组）"""
    result = await db.execute(
        select(AgentType)
        .where(AgentType.is_active == True)
        .order_by(AgentType.sort_order)
    )
    agent_types = result.scalars().all()
    
    # 按层级分组
    layer_0 = []
    layer_1 = []
    layer_2 = []
    orchestrator = []
    
    for at in agent_types:
        core_metrics = [m.metric for m in at.metric_mappings if m.is_core]
        at_with_metrics = AgentTypeWithMetrics(
            **{k: v for k, v in at.__dict__.items() if not k.startswith('_')},
            metric_mappings=at.metric_mappings,
            core_metrics=core_metrics
        )
        if at.layer == "layer_0":
            layer_0.append(at_with_metrics)
        elif at.layer == "layer_1":
            layer_1.append(at_with_metrics)
        elif at.layer == "layer_2":
            layer_2.append(at_with_metrics)
        elif at.layer == "orchestrator":
            orchestrator.append(at_with_metrics)
    
    return AgentTypeOverview(
        layer_0=layer_0,
        layer_1=layer_1,
        layer_2=layer_2,
        orchestrator=orchestrator,
        total_agent_types=len(agent_types)
    )


# ==================== 初始化内置 Agent 类型 ====================

@router.post("/init-agent-types")
async def init_builtin_agent_types(db: AsyncSession = Depends(get_db)):
    """初始化内置 Agent 类型（基于 TanQi AI Agent 架构）"""
    
    # 检查是否已初始化
    result = await db.execute(
        select(AgentType).where(AgentType.code == "search_card")
    )
    if result.scalar_one_or_none():
        return {"message": "内置Agent类型已存在", "initialized": False}
    
    # ========== 创建 Agent 类型 ==========
    agent_types_data = [
        # Layer 0 - 数据采集
        {
            "name": "搜索卡片", "code": "search_card", "layer": "layer_0",
            "card_type": "search", "class_name": "SearchCardAgent",
            "description": "网络搜索、信息汇总、来源验证",
            "sort_order": 1,
            "execution_flow": {
                "nodes": ["query_analysis", "multi_search", "result_aggregation", "bubble_report"],
                "description": "用户Query → 多维度搜索策略规划 → 工具调用循环 → 结果汇总 → 冒泡上报"
            },
            "io_definition": {
                "input": ["search_query", "search_results", "task_instruction"],
                "output": ["markdown_summary", "SearchCardResponse", "CardSignal"]
            },
            "available_tools": ["web_search", "browse_url", "sandbox_content_reader", "bubble_finding"]
        },
        {
            "name": "社媒卡片", "code": "social_media_card", "layer": "layer_0",
            "card_type": "social_media", "class_name": "SocialMediaCardAgent",
            "description": "X/YouTube/Telegram 社媒情报搜集",
            "sort_order": 2,
            "available_tools": ["social_search", "bubble_finding"]
        },
        {
            "name": "公司卡片", "code": "company_card", "layer": "layer_0",
            "card_type": "company", "class_name": "CompanyCardAgent",
            "description": "企业信息查询和分析",
            "sort_order": 3,
            "available_tools": ["company_search", "bubble_finding"]
        },
        {
            "name": "靖企卡片", "code": "jingqi_card", "layer": "layer_0",
            "card_type": "jingqi", "class_name": "JingqiCardAgent",
            "description": "靖企数据库查询",
            "sort_order": 4,
            "available_tools": ["jingqi_query", "bubble_finding"]
        },
        {
            "name": "文件卡片", "code": "file_card", "layer": "layer_0",
            "card_type": "file", "class_name": "FileCardAgent",
            "description": "PDF/Excel/CSV/图片等文件解析",
            "sort_order": 5,
            "available_tools": ["file_parser", "bubble_finding"]
        },
        
        # Layer 1 - 数据分析/可视化
        {
            "name": "图表卡片", "code": "chart_card", "layer": "layer_1",
            "card_type": "chart", "class_name": "ChartCardAgent",
            "description": "ECharts 图表代码生成",
            "sort_order": 10,
            "execution_flow": {
                "nodes": ["data_analysis", "code_generation", "compile_gate", "upload"],
                "description": "需求分析 → 数据处理 → 代码生成 → 编译验证 → 代码上传"
            },
            "io_definition": {
                "input": ["data_source", "chart_requirement", "saved_code"],
                "output": ["tsx_code", "chart_url", "compile_result"]
            },
            "available_tools": ["get_server_file"]
        },
        {
            "name": "地图卡片", "code": "map_card", "layer": "layer_1",
            "card_type": "map", "class_name": "MapCardAgent",
            "description": "Mapbox 地图可视化代码生成",
            "sort_order": 11,
            "available_tools": ["get_server_file"]
        },
        {
            "name": "网络图卡片", "code": "network_card", "layer": "layer_1",
            "card_type": "network", "class_name": "NetworkCardAgent",
            "description": "G6 关系网络图代码生成",
            "sort_order": 12,
            "available_tools": ["get_server_file"]
        },
        {
            "name": "时间线卡片", "code": "timeline_card", "layer": "layer_1",
            "card_type": "timeline", "class_name": "TimelineCardAgent",
            "description": "时间线可视化代码生成",
            "sort_order": 13,
            "available_tools": ["get_server_file"]
        },
        
        # Layer 2 - 报告生成
        {
            "name": "报告卡片", "code": "report_card", "layer": "layer_2",
            "card_type": "report_v2", "class_name": "ReportCardAgentV2",
            "description": "TSX 报告生成、多章节结构化报告",
            "sort_order": 20,
            "execution_flow": {
                "nodes": ["context_collection", "chapter_planning", "chapter_generation", "chapter_compile", "report_assembly", "upload"],
                "description": "上下文收集 → 章节规划 → 逐章生成 → 章节编译 → 报告组装 → 上传"
            },
            "io_definition": {
                "input": ["investigation_context", "report_title", "chapter_structure"],
                "output": ["tsx_report", "report_url", "chapter_list"]
            },
            "available_tools": ["assemble_report", "get_server_file"]
        },
        
        # Orchestrator - 编排层
        {
            "name": "主Agent", "code": "main_agent", "layer": "orchestrator",
            "card_type": None, "class_name": "MainAgent",
            "description": "用户意图理解、任务分解、子代理协调",
            "sort_order": 0,
            "execution_flow": {
                "nodes": ["intent_understanding", "task_decomposition", "card_creation", "task_orchestration", "result_aggregation"],
                "description": "意图理解 → 任务分解 → 卡片创建 → 任务编排 → 结果聚合"
            }
        },
        {
            "name": "任务编排器", "code": "task_orchestrator", "layer": "orchestrator",
            "card_type": None, "class_name": "TaskOrchestrator",
            "description": "管理并行任务执行、分析依赖、构建执行层级",
            "sort_order": 1
        }
    ]
    
    agent_type_map = {}
    for at_data in agent_types_data:
        agent_type = AgentType(**at_data)
        db.add(agent_type)
        await db.flush()
        agent_type_map[at_data["code"]] = agent_type.id
    
    # ========== 创建 Agent 类型与指标的映射 ==========
    # 获取已有指标
    metrics_result = await db.execute(select(MetricDefinition))
    metrics = {m.code: m.id for m in metrics_result.scalars().all()}
    
    # 定义映射关系
    mappings_data = [
        # 搜索卡片的核心指标
        {"agent_code": "search_card", "metric_code": "tool_call_success_rate", "is_core": True},
        {"agent_code": "search_card", "metric_code": "tool_selection_accuracy", "is_core": True},
        {"agent_code": "search_card", "metric_code": "response_relevance", "is_core": False},
        {"agent_code": "search_card", "metric_code": "info_completeness", "is_core": False},
        
        # 图表卡片的核心指标
        {"agent_code": "chart_card", "metric_code": "code_execution_success", "is_core": True},
        {"agent_code": "chart_card", "metric_code": "visualization_quality", "is_core": True},
        {"agent_code": "chart_card", "metric_code": "output_accuracy", "is_core": False},
        
        # 地图卡片的核心指标
        {"agent_code": "map_card", "metric_code": "code_execution_success", "is_core": True},
        {"agent_code": "map_card", "metric_code": "visualization_quality", "is_core": True},
        
        # 网络图卡片的核心指标
        {"agent_code": "network_card", "metric_code": "code_execution_success", "is_core": True},
        {"agent_code": "network_card", "metric_code": "visualization_quality", "is_core": True},
        
        # 时间线卡片的核心指标
        {"agent_code": "timeline_card", "metric_code": "code_execution_success", "is_core": True},
        {"agent_code": "timeline_card", "metric_code": "visualization_quality", "is_core": True},
        
        # 报告卡片的核心指标
        {"agent_code": "report_card", "metric_code": "task_completion", "is_core": True, "weight_override": 2.5},
        {"agent_code": "report_card", "metric_code": "info_completeness", "is_core": True, "weight_override": 2.0},
        {"agent_code": "report_card", "metric_code": "code_execution_success", "is_core": True},
        {"agent_code": "report_card", "metric_code": "output_accuracy", "is_core": False},
        
        # 主Agent的核心指标
        {"agent_code": "main_agent", "metric_code": "plan_quality", "is_core": True, "weight_override": 2.0},
        {"agent_code": "main_agent", "metric_code": "parallel_efficiency", "is_core": True},
        {"agent_code": "main_agent", "metric_code": "delegate_success_rate", "is_core": True},
        {"agent_code": "main_agent", "metric_code": "e2e_latency", "is_core": False},
        {"agent_code": "main_agent", "metric_code": "task_success_rate", "is_core": False},
    ]
    
    for mapping_data in mappings_data:
        agent_type_id = agent_type_map.get(mapping_data["agent_code"])
        metric_id = metrics.get(mapping_data["metric_code"])
        if agent_type_id and metric_id:
            mapping = AgentMetricMapping(
                agent_type_id=agent_type_id,
                metric_id=metric_id,
                is_core=mapping_data.get("is_core", False),
                weight_override=mapping_data.get("weight_override")
            )
            db.add(mapping)
    
    await db.commit()
    
    return {
        "message": "内置Agent类型初始化成功",
        "initialized": True,
        "agent_types": len(agent_types_data),
        "mappings": len(mappings_data)
    }
