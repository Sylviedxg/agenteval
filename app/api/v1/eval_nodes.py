"""
评测节点 API - 基于 tanqi_eval_v2.xlsx 设计
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.eval_node import (
    EvalNodeDefinition, GateDefinition, NodeScoreResult,
    GateCheckResult, LayerAggregateScore, InvestigationScore
)
from app.schemas.eval_node import (
    EvalNodeDefinitionCreate, EvalNodeDefinitionResponse,
    GateDefinitionCreate, GateDefinitionResponse,
    NodeScoreResultResponse, NodeScoreResultUpdate,
    GateCheckResultResponse,
    LayerAggregateScoreResponse,
    InvestigationScoreResponse,
    EvalNodeOverview, TraceEvalResult
)

router = APIRouter(prefix="/eval-nodes", tags=["评测节点"])


# ==================== 节点定义 ====================

@router.get("/definitions", response_model=List[EvalNodeDefinitionResponse])
async def list_node_definitions(
    eval_layer: Optional[str] = None,
    agent_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取节点定义列表"""
    query = select(EvalNodeDefinition).where(EvalNodeDefinition.is_active == True)
    if eval_layer:
        query = query.where(EvalNodeDefinition.eval_layer == eval_layer)
    if agent_name:
        query = query.where(EvalNodeDefinition.agent_name == agent_name)
    query = query.order_by(EvalNodeDefinition.sort_order)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/definitions/{node_code}", response_model=EvalNodeDefinitionResponse)
async def get_node_definition(node_code: str, db: AsyncSession = Depends(get_db)):
    """获取单个节点定义"""
    result = await db.execute(
        select(EvalNodeDefinition).where(EvalNodeDefinition.node_code == node_code)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    return node


# ==================== Gate定义 ====================

@router.get("/gates", response_model=List[GateDefinitionResponse])
async def list_gate_definitions(db: AsyncSession = Depends(get_db)):
    """获取Gate定义列表"""
    result = await db.execute(
        select(GateDefinition)
        .where(GateDefinition.is_active == True)
        .order_by(GateDefinition.sort_order)
    )
    return result.scalars().all()


# ==================== 概览 ====================

@router.get("/overview", response_model=EvalNodeOverview)
async def get_eval_overview(db: AsyncSession = Depends(get_db)):
    """获取评测节点概览"""
    # 获取所有节点
    nodes_result = await db.execute(
        select(EvalNodeDefinition)
        .where(EvalNodeDefinition.is_active == True)
        .order_by(EvalNodeDefinition.sort_order)
    )
    nodes = nodes_result.scalars().all()
    
    # 获取所有Gate
    gates_result = await db.execute(
        select(GateDefinition)
        .where(GateDefinition.is_active == True)
        .order_by(GateDefinition.sort_order)
    )
    gates = gates_result.scalars().all()
    
    # 按层级分组
    l0_nodes = [n for n in nodes if n.eval_layer == "L0 MainAgent"]
    l1_nodes = [n for n in nodes if n.eval_layer == "L1 单体"]
    l2_nodes = [n for n in nodes if n.eval_layer == "L2 协作"]
    l3_nodes = [n for n in nodes if n.eval_layer == "L3 系统"]
    
    return EvalNodeOverview(
        total_nodes=len(nodes),
        l0_nodes=l0_nodes,
        l1_nodes=l1_nodes,
        l2_nodes=l2_nodes,
        l3_nodes=l3_nodes,
        gates=gates
    )


# ==================== Trace评测结果 ====================

@router.get("/trace/{trace_id}/results", response_model=TraceEvalResult)
async def get_trace_eval_results(trace_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取单次Trace的完整评测结果"""
    # 获取Investigation总分
    inv_result = await db.execute(
        select(InvestigationScore).where(InvestigationScore.trace_id == trace_id)
    )
    investigation_score = inv_result.scalar_one_or_none()
    
    # 获取层级得分
    layer_result = await db.execute(
        select(LayerAggregateScore).where(LayerAggregateScore.trace_id == trace_id)
    )
    layer_scores = layer_result.scalars().all()
    
    # 获取节点得分
    node_result = await db.execute(
        select(NodeScoreResult).where(NodeScoreResult.trace_id == trace_id)
    )
    node_scores = node_result.scalars().all()
    
    # 获取Gate结果
    gate_result = await db.execute(
        select(GateCheckResult).where(GateCheckResult.trace_id == trace_id)
    )
    gate_results = gate_result.scalars().all()
    
    # 需要人工复核的节点
    human_review_nodes = [
        ns.node_definition.node_code 
        for ns in node_scores 
        if ns.needs_human_review and not ns.human_reviewed
    ]
    
    return TraceEvalResult(
        trace_id=trace_id,
        investigation_score=investigation_score,
        layer_scores=list(layer_scores),
        node_scores=list(node_scores),
        gate_results=list(gate_results),
        needs_human_review=len(human_review_nodes) > 0,
        human_review_nodes=human_review_nodes
    )


# ==================== 人工复核 ====================

@router.get("/human-review/pending", response_model=List[NodeScoreResultResponse])
async def list_pending_human_review(db: AsyncSession = Depends(get_db)):
    """获取待人工复核的节点评分"""
    result = await db.execute(
        select(NodeScoreResult)
        .where(NodeScoreResult.needs_human_review == True)
        .where(NodeScoreResult.human_reviewed == False)
        .order_by(NodeScoreResult.created_at)
    )
    return result.scalars().all()


@router.put("/human-review/{score_id}", response_model=NodeScoreResultResponse)
async def submit_human_review(
    score_id: UUID,
    data: NodeScoreResultUpdate,
    db: AsyncSession = Depends(get_db)
):
    """提交人工复核结果"""
    result = await db.execute(
        select(NodeScoreResult).where(NodeScoreResult.id == score_id)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail="评分记录不存在")
    
    # 更新人工评分
    if data.subj_metric_1_human_score is not None:
        score.subj_metric_1_human_score = data.subj_metric_1_human_score
        score.subj_metric_1_final = data.subj_metric_1_human_score
    
    if data.subj_metric_2_human_score is not None:
        score.subj_metric_2_human_score = data.subj_metric_2_human_score
        score.subj_metric_2_final = data.subj_metric_2_human_score
    
    # 重新计算主观得分和最终得分
    subj_scores = []
    if score.subj_metric_1_final:
        subj_scores.append(score.subj_metric_1_final)
    if score.subj_metric_2_final:
        subj_scores.append(score.subj_metric_2_final)
    
    if subj_scores:
        score.subj_score = sum(subj_scores) / len(subj_scores) / 5  # 归一化到0-1
    
    if score.obj_score is not None and score.subj_score is not None:
        score.final_score = score.obj_score * 0.7 + score.subj_score * 0.3
    
    score.human_reviewed = True
    score.human_reviewer = data.human_reviewer
    
    await db.commit()
    await db.refresh(score)
    return score


# ==================== 初始化33个节点 ====================

@router.post("/init-nodes")
async def init_eval_nodes(db: AsyncSession = Depends(get_db)):
    """初始化33个评测节点（基于tanqi_eval_v2.xlsx）"""
    
    # 检查是否已初始化
    result = await db.execute(
        select(EvalNodeDefinition).where(EvalNodeDefinition.node_code == "main_llm_call")
    )
    if result.scalar_one_or_none():
        return {"message": "节点已初始化", "initialized": False}
    
    # 33个节点定义（按表格顺序）
    nodes_data = [
        # ========== L0 MainAgent (6个节点) ==========
        {
            "agent_name": "MainAgent",
            "node_name": "LLM调用(意图理解+规划)",
            "node_code": "main_llm_call",
            "layer_tag": "-",
            "eval_layer": "L0 MainAgent",
            "obj_metric_1_name": "LLM调用成功率",
            "obj_metric_1_source": "Langfuse success/failure",
            "obj_metric_2_name": "首token延迟",
            "obj_metric_2_source": "Langfuse duration(ms)",
            "subj_metric_1_name": "意图理解准确性",
            "subj_metric_1_method": "LLM初评+人工复核（1-5分）",
            "subj_metric_2_name": "规划合理性",
            "subj_metric_2_method": "LLM初评+人工复核（1-5分）",
            "obj_score_formula": "成功率*0.6 + TTFT达标*0.4",
            "subj_score_formula": "(理解+规划)/10",
            "belongs_to": "MainAgent",
            "layer_weight": "Layer0权重30%",
            "node_weight_rule": "LLM节点权重×1.5",
            "is_gate": True,
            "gate_type": "Gate0",
            "gate_condition": "输出结构合规+plan合理",
            "remark": "Gate0来源节点",
            "sort_order": 1
        },
        {
            "agent_name": "MainAgent",
            "node_name": "plan_parallel（规划+路由）",
            "node_code": "main_plan_parallel",
            "layer_tag": "-",
            "eval_layer": "L0 MainAgent",
            "obj_metric_1_name": "任务类型覆盖率",
            "obj_metric_1_source": "实际task_type/应有task_type",
            "obj_metric_2_name": "依赖层级正确性",
            "obj_metric_2_source": "有无循环依赖（0/1）",
            "subj_metric_1_name": "任务分解合理性",
            "subj_metric_1_method": "LLM初评（1-5分）",
            "obj_score_formula": "覆盖率*0.6 + 无循环*0.4",
            "subj_score_formula": "分解合理性/5",
            "belongs_to": "MainAgent",
            "layer_weight": "Layer0权重30%",
            "node_weight_rule": "节点均分",
            "sort_order": 2
        },
        {
            "agent_name": "MainAgent",
            "node_name": "delegate_to_card（执行委派）",
            "node_code": "main_delegate",
            "layer_tag": "-",
            "eval_layer": "L0 MainAgent",
            "obj_metric_1_name": "card创建成功率",
            "obj_metric_1_source": "成功创建数/委派总数",
            "obj_metric_2_name": "card_type匹配率",
            "obj_metric_2_source": "实际类型/规划类型一致比例",
            "obj_score_formula": "创建成功*0.5 + 类型匹配*0.5",
            "belongs_to": "MainAgent",
            "layer_weight": "Layer0权重30%",
            "node_weight_rule": "节点均分",
            "sort_order": 3
        },
        {
            "agent_name": "MainAgent",
            "node_name": "write_todos（任务状态记录）",
            "node_code": "main_write_todos",
            "layer_tag": "-",
            "eval_layer": "L0 MainAgent",
            "obj_metric_1_name": "todos写入完整性",
            "obj_metric_1_source": "实际写入字段/应写入字段",
            "obj_metric_2_name": "与实际执行一致性",
            "obj_metric_2_source": "todos状态与card状态比对",
            "obj_score_formula": "完整性*0.5 + 一致性*0.5",
            "belongs_to": "MainAgent",
            "layer_weight": "Layer0权重30%",
            "node_weight_rule": "节点均分",
            "sort_order": 4
        },
        
        # ========== L1 单体 - CardAgent通用 (5个节点) ==========
        {
            "agent_name": "CardAgent(通用)",
            "node_name": "_build_card_system_prompt",
            "node_code": "card_build_prompt",
            "layer_tag": "Layer0/1/2",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "prompt构建成功率",
            "obj_metric_1_source": "成功/失败（1/0）",
            "obj_metric_2_name": "上下文信息完整性",
            "obj_metric_2_source": "必填上下文字段覆盖率",
            "obj_score_formula": "成功*0.5 + 完整性*0.5",
            "belongs_to": "CardAgent",
            "layer_weight": "按所属Layer",
            "node_weight_rule": "通用节点均分",
            "sort_order": 10
        },
        {
            "agent_name": "CardAgent(通用)",
            "node_name": "LLM推理(run_stream_loop)",
            "node_code": "card_llm_inference",
            "layer_tag": "Layer0/1/2",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "TTFT首token延迟",
            "obj_metric_1_source": "Langfuse duration(ms)",
            "obj_metric_2_name": "工具调用次数",
            "obj_metric_2_source": "Langfuse tool_call count",
            "subj_metric_1_name": "推理质量",
            "subj_metric_1_method": "LLM初评（1-5分）",
            "obj_score_formula": "TTFT达标*0.5 + 调用次数合理*0.5",
            "subj_score_formula": "推理质量/5",
            "belongs_to": "CardAgent",
            "layer_weight": "按所属Layer",
            "node_weight_rule": "通用节点均分",
            "sort_order": 11
        },
        {
            "agent_name": "CardAgent(通用)",
            "node_name": "工具调用循环(Tool Calls)",
            "node_code": "card_tool_calls",
            "layer_tag": "Layer0/1/2",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "工具调用成功率",
            "obj_metric_1_source": "成功次数/总次数",
            "obj_metric_2_name": "重试次数",
            "obj_metric_2_source": "Langfuse retry count",
            "obj_score_formula": "成功率*0.7 + 重试少*0.3",
            "belongs_to": "CardAgent",
            "layer_weight": "按所属Layer",
            "node_weight_rule": "通用节点均分",
            "sort_order": 12
        },
        {
            "agent_name": "CardAgent(通用)",
            "node_name": "EvidenceCapability(冒泡上报)",
            "node_code": "card_bubble",
            "layer_tag": "Layer0/1/2",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "冒泡数量",
            "obj_metric_1_source": "bubble_finding count",
            "obj_metric_2_name": "冒泡触发率",
            "obj_metric_2_source": "有输出的card中触发冒泡的比例",
            "subj_metric_1_name": "冒泡内容质量",
            "subj_metric_1_method": "LLM初评（1-5分）",
            "obj_score_formula": "数量达标*0.5 + 触发率*0.5",
            "subj_score_formula": "内容质量/5",
            "belongs_to": "CardAgent",
            "layer_weight": "按所属Layer",
            "node_weight_rule": "通用节点均分",
            "sort_order": 13
        },
        {
            "agent_name": "CardAgent(通用)",
            "node_name": "OutputCapability(输出写入)",
            "node_code": "card_output",
            "layer_tag": "Layer0/1/2",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "输出写入成功率",
            "obj_metric_1_source": "成功写入/应写入（1/0）",
            "obj_metric_2_name": "索引完整性",
            "obj_metric_2_source": "索引字段覆盖率",
            "obj_score_formula": "写入成功*0.6 + 索引完整*0.4",
            "belongs_to": "CardAgent",
            "layer_weight": "按所属Layer",
            "node_weight_rule": "通用节点均分",
            "sort_order": 14
        },
        
        # ========== L1 单体 - SearchCardAgent (4个节点) ==========
        {
            "agent_name": "SearchCardAgent",
            "node_name": "多维度搜索策略规划",
            "node_code": "search_strategy",
            "layer_tag": "Layer0",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "搜索策略多样性",
            "obj_metric_1_source": "不同关键词维度数",
            "obj_metric_2_name": "关键词覆盖率",
            "obj_metric_2_source": "覆盖query实体数/query总实体数",
            "subj_metric_1_name": "策略合理性",
            "subj_metric_1_method": "LLM初评（1-5分）",
            "obj_score_formula": "多样性*0.4 + 覆盖率*0.6",
            "subj_score_formula": "策略合理性/5",
            "belongs_to": "SearchCardAgent",
            "layer_weight": "Layer0权重30%",
            "node_weight_rule": "Search节点均分",
            "sort_order": 20
        },
        {
            "agent_name": "SearchCardAgent",
            "node_name": "web_search工具调用",
            "node_code": "search_web_search",
            "layer_tag": "Layer0",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "搜索成功率",
            "obj_metric_1_source": "成功次数/总次数",
            "obj_metric_2_name": "搜索次数",
            "obj_metric_2_source": "Langfuse tool_call count",
            "obj_score_formula": "成功率*0.7 + 次数合理*0.3",
            "belongs_to": "SearchCardAgent",
            "layer_weight": "Layer0权重30%",
            "node_weight_rule": "Search节点均分",
            "sort_order": 21
        },
        {
            "agent_name": "SearchCardAgent",
            "node_name": "browse_url网页提取",
            "node_code": "search_browse_url",
            "layer_tag": "Layer0",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "提取成功率",
            "obj_metric_1_source": "成功URL数/尝试URL数",
            "obj_metric_2_name": "browse_url调用次数",
            "obj_metric_2_source": "Langfuse count",
            "obj_score_formula": "成功率*0.7 + 次数合理*0.3",
            "belongs_to": "SearchCardAgent",
            "layer_weight": "Layer0权重30%",
            "node_weight_rule": "Search节点均分",
            "sort_order": 22
        },
        {
            "agent_name": "SearchCardAgent",
            "node_name": "结果汇总输出",
            "node_code": "search_result_summary",
            "layer_tag": "Layer0",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "输出覆盖搜索结果比例",
            "obj_metric_1_source": "引用来源数/总搜索结果数",
            "obj_metric_2_name": "去重率",
            "obj_metric_2_source": "去重后条目/去重前条目",
            "subj_metric_1_name": "汇总质量",
            "subj_metric_1_method": "LLM初评+人工复核（1-5分）",
            "obj_score_formula": "覆盖率*0.6 + 去重率*0.4",
            "subj_score_formula": "汇总质量/5",
            "belongs_to": "SearchCardAgent",
            "layer_weight": "Layer0权重30%",
            "node_weight_rule": "结果汇总节点权重×1.5（GateA来源）",
            "is_gate": True,
            "gate_type": "GateA",
            "gate_condition": "召回覆盖度达标+evidence完整",
            "sort_order": 23
        },
        
        # ========== L1 单体 - ChartCardAgent (3个节点) ==========
        {
            "agent_name": "ChartCardAgent",
            "node_name": "需求分析+数据获取",
            "node_code": "chart_data_fetch",
            "layer_tag": "Layer1",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "数据源获取成功率",
            "obj_metric_1_source": "Langfuse tool_call success",
            "obj_metric_2_name": "数据获取耗时",
            "obj_metric_2_source": "Langfuse duration(ms)",
            "subj_metric_1_name": "需求理解准确性",
            "subj_metric_1_method": "LLM初评（1-5分）",
            "obj_score_formula": "成功率*0.6 + 耗时达标*0.4",
            "subj_score_formula": "需求理解/5",
            "belongs_to": "ChartCardAgent",
            "layer_weight": "Layer1权重30%",
            "node_weight_rule": "Viz节点均分",
            "sort_order": 30
        },
        {
            "agent_name": "ChartCardAgent",
            "node_name": "TSX代码生成(ECharts)",
            "node_code": "chart_code_gen",
            "layer_tag": "Layer1",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "代码生成耗时",
            "obj_metric_1_source": "Langfuse duration(ms)",
            "obj_metric_2_name": "代码行数合理性",
            "obj_metric_2_source": "实际行数/基准行数范围",
            "subj_metric_1_name": "代码质量",
            "subj_metric_1_method": "LLM初评（1-5分）",
            "obj_score_formula": "耗时达标*0.5 + 行数合理*0.5",
            "subj_score_formula": "代码质量/5",
            "belongs_to": "ChartCardAgent",
            "layer_weight": "Layer1权重30%",
            "node_weight_rule": "Viz节点均分",
            "sort_order": 31
        },
        {
            "agent_name": "ChartCardAgent",
            "node_name": "VisualizationCompileGate",
            "node_code": "chart_compile_gate",
            "layer_tag": "Layer1",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "编译成功率",
            "obj_metric_1_source": "最终编译success/failure",
            "obj_metric_2_name": "编译轮次",
            "obj_metric_2_source": "Langfuse rounds_used",
            "obj_metric_3_name": "编译耗时",
            "obj_metric_3_source": "Langfuse duration(ms)",
            "subj_metric_1_name": "渲染正确性",
            "subj_metric_1_method": "人工复核（1-5分）",
            "obj_score_formula": "成功*0.5 + 轮次少*0.3 + 耗时达标*0.2",
            "subj_score_formula": "渲染/5",
            "belongs_to": "ChartCardAgent",
            "layer_weight": "Layer1权重30%",
            "node_weight_rule": "CompileGate节点权重×1.5（GateB来源）",
            "is_gate": True,
            "gate_type": "GateB",
            "gate_condition": "编译success",
            "sort_order": 32
        },
        
        # ========== L1 单体 - MapCardAgent (2个节点) ==========
        {
            "agent_name": "MapCardAgent",
            "node_name": "坐标处理+代码生成(Mapbox)",
            "node_code": "map_code_gen",
            "layer_tag": "Layer1",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "坐标解析成功率",
            "obj_metric_1_source": "有效坐标数/总坐标数",
            "obj_metric_2_name": "代码生成耗时",
            "obj_metric_2_source": "Langfuse duration(ms)",
            "subj_metric_1_name": "地图样式合理性",
            "subj_metric_1_method": "人工复核（1-5分）",
            "obj_score_formula": "解析率*0.6 + 耗时达标*0.4",
            "subj_score_formula": "样式/5",
            "belongs_to": "MapCardAgent",
            "layer_weight": "Layer1权重30%",
            "node_weight_rule": "Viz节点均分",
            "sort_order": 33
        },
        {
            "agent_name": "MapCardAgent",
            "node_name": "VisualizationCompileGate",
            "node_code": "map_compile_gate",
            "layer_tag": "Layer1",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "编译成功率",
            "obj_metric_1_source": "success/failure",
            "obj_metric_2_name": "编译轮次",
            "obj_metric_2_source": "Langfuse rounds_used",
            "obj_metric_3_name": "编译耗时",
            "obj_metric_3_source": "Langfuse duration(ms)",
            "subj_metric_1_name": "渲染正确性",
            "subj_metric_1_method": "人工复核（1-5分）",
            "obj_score_formula": "成功*0.5 + 轮次少*0.3 + 耗时达标*0.2",
            "subj_score_formula": "渲染/5",
            "belongs_to": "MapCardAgent",
            "layer_weight": "Layer1权重30%",
            "node_weight_rule": "CompileGate节点权重×1.5（GateB来源）",
            "is_gate": True,
            "gate_type": "GateB",
            "gate_condition": "编译success",
            "sort_order": 34
        },
        
        # ========== L1 单体 - NetworkCardAgent (2个节点) ==========
        {
            "agent_name": "NetworkCardAgent",
            "node_name": "关系数据处理+代码生成(G6)",
            "node_code": "network_code_gen",
            "layer_tag": "Layer1",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "节点/边解析完整性",
            "obj_metric_1_source": "实际解析数/数据源总数",
            "obj_metric_2_name": "代码生成耗时",
            "obj_metric_2_source": "Langfuse duration(ms)",
            "subj_metric_1_name": "关系图布局合理性",
            "subj_metric_1_method": "人工复核（1-5分）",
            "subj_metric_2_name": "节点渲染完整性",
            "subj_metric_2_method": "LLM初评（1-5分）",
            "obj_score_formula": "解析率*0.6 + 耗时达标*0.4",
            "subj_score_formula": "(布局+渲染)/10",
            "belongs_to": "NetworkCardAgent",
            "layer_weight": "Layer1权重30%",
            "node_weight_rule": "Viz节点均分",
            "sort_order": 35
        },
        {
            "agent_name": "NetworkCardAgent",
            "node_name": "VisualizationCompileGate",
            "node_code": "network_compile_gate",
            "layer_tag": "Layer1",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "编译成功率",
            "obj_metric_1_source": "success/failure",
            "obj_metric_2_name": "编译轮次",
            "obj_metric_2_source": "Langfuse rounds_used",
            "obj_metric_3_name": "编译耗时",
            "obj_metric_3_source": "Langfuse duration(ms)",
            "subj_metric_1_name": "渲染正确性",
            "subj_metric_1_method": "人工复核（1-5分）",
            "obj_score_formula": "成功*0.5 + 轮次少*0.3 + 耗时达标*0.2",
            "subj_score_formula": "渲染/5",
            "belongs_to": "NetworkCardAgent",
            "layer_weight": "Layer1权重30%",
            "node_weight_rule": "CompileGate节点权重×1.5（GateB来源）",
            "is_gate": True,
            "gate_type": "GateB",
            "gate_condition": "编译success",
            "sort_order": 36
        },
        
        # ========== L1 单体 - TimelineCardAgent (2个节点) ==========
        {
            "agent_name": "TimelineCardAgent",
            "node_name": "时间线数据处理+代码生成",
            "node_code": "timeline_code_gen",
            "layer_tag": "Layer1",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "时间节点解析完整性",
            "obj_metric_1_source": "有效时间节点数/总节点数",
            "obj_metric_2_name": "代码生成耗时",
            "obj_metric_2_source": "Langfuse duration(ms)",
            "subj_metric_1_name": "时序逻辑正确性",
            "subj_metric_1_method": "LLM初评+人工复核（1-5分）",
            "subj_metric_2_name": "事件覆盖完整性",
            "subj_metric_2_method": "LLM初评（1-5分）",
            "obj_score_formula": "解析率*0.6 + 耗时达标*0.4",
            "subj_score_formula": "(时序+覆盖)/10",
            "belongs_to": "TimelineCardAgent",
            "layer_weight": "Layer1权重30%",
            "node_weight_rule": "Viz节点均分",
            "sort_order": 37
        },
        {
            "agent_name": "TimelineCardAgent",
            "node_name": "VisualizationCompileGate",
            "node_code": "timeline_compile_gate",
            "layer_tag": "Layer1",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "编译成功率",
            "obj_metric_1_source": "success/failure",
            "obj_metric_2_name": "编译轮次",
            "obj_metric_2_source": "Langfuse rounds_used",
            "obj_metric_3_name": "编译耗时",
            "obj_metric_3_source": "Langfuse duration(ms)",
            "subj_metric_1_name": "渲染正确性",
            "subj_metric_1_method": "人工复核（1-5分）",
            "obj_score_formula": "成功*0.5 + 轮次少*0.3 + 耗时达标*0.2",
            "subj_score_formula": "渲染/5",
            "belongs_to": "TimelineCardAgent",
            "layer_weight": "Layer1权重30%",
            "node_weight_rule": "CompileGate节点权重×1.5（GateB来源）",
            "is_gate": True,
            "gate_type": "GateB",
            "gate_condition": "编译success",
            "sort_order": 38
        },
        
        # ========== L1 单体 - ReportCardAgentV2 (6个节点) ==========
        {
            "agent_name": "ReportCardAgentV2",
            "node_name": "_collect_visual_cards(上下文收集)",
            "node_code": "report_collect_context",
            "layer_tag": "Layer2",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "可视化card覆盖率",
            "obj_metric_1_source": "收集到的viz card数/Layer1总card数",
            "obj_metric_2_name": "evidence收集完整性",
            "obj_metric_2_source": "evidence条目数/冒泡总数",
            "subj_metric_1_name": "上下文与query相关性",
            "subj_metric_1_method": "LLM初评（1-5分）",
            "obj_score_formula": "覆盖率*0.5 + 完整性*0.5",
            "subj_score_formula": "相关性/5",
            "belongs_to": "ReportCardAgentV2",
            "layer_weight": "Layer2权重40%",
            "node_weight_rule": "Report节点均分",
            "is_gate": True,
            "gate_type": "GateB",
            "gate_condition": "Layer1全部completed",
            "remark": "Layer2入口节点",
            "sort_order": 40
        },
        {
            "agent_name": "ReportCardAgentV2",
            "node_name": "build_ownership_plan(章节规划)",
            "node_code": "report_chapter_plan",
            "layer_tag": "Layer2",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "章节数量合理性",
            "obj_metric_1_source": "章节数/query复杂度基准",
            "obj_metric_2_name": "章节覆盖完整性",
            "obj_metric_2_source": "覆盖query维度数/query总维度",
            "subj_metric_1_name": "章节结构质量",
            "subj_metric_1_method": "LLM初评+人工复核（1-5分）",
            "obj_score_formula": "数量合理*0.4 + 覆盖率*0.6",
            "subj_score_formula": "结构质量/5",
            "belongs_to": "ReportCardAgentV2",
            "layer_weight": "Layer2权重40%",
            "node_weight_rule": "Report节点均分",
            "remark": "规划质量直接影响报告结构",
            "sort_order": 41
        },
        {
            "agent_name": "ReportCardAgentV2",
            "node_name": "chapter_writer SubAgent(逐章生成)",
            "node_code": "report_chapter_write",
            "layer_tag": "Layer2",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "章节生成耗时",
            "obj_metric_1_source": "Langfuse duration(ms)",
            "obj_metric_2_name": "章节引用evidence数",
            "obj_metric_2_source": "每章引用evidence条数",
            "obj_metric_3_name": "可视化复用率",
            "obj_metric_3_source": "复用viz组件数/总可用viz数",
            "subj_metric_1_name": "章节内容完整性",
            "subj_metric_1_method": "LLM初评+人工复核（1-5分）",
            "subj_metric_2_name": "章节论述质量",
            "subj_metric_2_method": "LLM初评+人工复核（1-5分）",
            "obj_score_formula": "耗时达标*0.3 + 引用率*0.4 + 复用率*0.3",
            "subj_score_formula": "(完整性+质量)/10",
            "belongs_to": "ReportCardAgentV2",
            "layer_weight": "Layer2权重40%",
            "node_weight_rule": "Report节点均分",
            "remark": "主观指标权重较高，内容质量是核心",
            "sort_order": 42
        },
        {
            "agent_name": "ReportCardAgentV2",
            "node_name": "ChapterGate(章节编译验证)",
            "node_code": "report_chapter_gate",
            "layer_tag": "Layer2",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "章节编译成功率",
            "obj_metric_1_source": "成功章节数/总章节数",
            "obj_metric_2_name": "总编译轮次",
            "obj_metric_2_source": "所有章节编译轮次之和",
            "obj_metric_3_name": "编译耗时",
            "obj_metric_3_source": "Langfuse duration(ms)",
            "subj_metric_1_name": "章节渲染正确性",
            "subj_metric_1_method": "人工复核（1-5分）",
            "obj_score_formula": "成功率*0.5 + 轮次少*0.3 + 耗时达标*0.2",
            "subj_score_formula": "渲染/5",
            "belongs_to": "ReportCardAgentV2",
            "layer_weight": "Layer2权重40%",
            "node_weight_rule": "Report节点均分",
            "is_gate": True,
            "gate_type": "GateC",
            "gate_condition": "所有章节编译success",
            "sort_order": 43
        },
        {
            "agent_name": "ReportCardAgentV2",
            "node_name": "assemble_report_chapters(报告组装)",
            "node_code": "report_assemble",
            "layer_tag": "Layer2",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "组装成功率",
            "obj_metric_1_source": "success/failure（1/0）",
            "obj_metric_2_name": "章节完整性",
            "obj_metric_2_source": "实际章节数/规划章节数",
            "obj_score_formula": "成功率*0.5 + 完整性*0.5",
            "final_score_formula": "客观*1.0（无主观）",
            "belongs_to": "ReportCardAgentV2",
            "layer_weight": "Layer2权重40%",
            "node_weight_rule": "Report节点均分",
            "is_gate": True,
            "gate_type": "GateC",
            "gate_condition": "章节数==规划数且组装成功",
            "remark": "纯工程节点",
            "sort_order": 44
        },
        {
            "agent_name": "ReportCardAgentV2",
            "node_name": "compile_gate(报告最终编译+上传)",
            "node_code": "report_final_compile",
            "layer_tag": "Layer2",
            "eval_layer": "L1 单体",
            "obj_metric_1_name": "最终编译成功率",
            "obj_metric_1_source": "success/failure",
            "obj_metric_2_name": "报告上传成功率",
            "obj_metric_2_source": "Langfuse upload status",
            "obj_metric_3_name": "总编译轮次",
            "obj_metric_3_source": "Langfuse rounds",
            "subj_metric_1_name": "报告完整性",
            "subj_metric_1_method": "LLM初评+人工复核（1-5分）",
            "subj_metric_2_name": "幻觉率",
            "subj_metric_2_method": "LLM初评+人工复核（幻觉断言占比，越低越好）",
            "obj_score_formula": "成功*0.4 + 上传*0.4 + 轮次少*0.2",
            "subj_score_formula": "(完整性 + (1-幻觉率)*5)/10",
            "belongs_to": "ReportCardAgentV2",
            "layer_weight": "Layer2权重40%",
            "node_weight_rule": "compile_gate节点权重×2.0（GateC+最终质量）",
            "is_gate": True,
            "gate_type": "GateC",
            "gate_condition": "编译success+上传成功+幻觉率<阈值",
            "remark": "最终质量关口，权重最高",
            "sort_order": 45
        },
        
        # ========== L2 协作层 (2个节点) ==========
        {
            "agent_name": "协作层",
            "node_name": "Layer0→Layer1数据交接",
            "node_code": "collab_l0_l1",
            "layer_tag": "Layer0→1",
            "eval_layer": "L2 协作",
            "obj_metric_1_name": "上游输出被下游引用率",
            "obj_metric_1_source": "Layer1实际引用的Layer0输出比例",
            "obj_metric_2_name": "冒泡链完整性",
            "obj_metric_2_source": "有效冒泡数/Layer0 card总数",
            "subj_metric_1_name": "跨卡片信息一致性",
            "subj_metric_1_method": "LLM初评（同一实体跨card矛盾检测，1-5分）",
            "obj_score_formula": "引用率*0.5 + 冒泡完整*0.5",
            "subj_score_formula": "一致性/5",
            "belongs_to": "协作层",
            "layer_weight": "Layer0权重30%",
            "node_weight_rule": "协作节点独立计算",
            "is_gate": True,
            "gate_type": "GateA",
            "gate_condition": "召回覆盖度达标+evidence完整",
            "remark": "数据断层的主要发生点",
            "sort_order": 50
        },
        {
            "agent_name": "协作层",
            "node_name": "Layer1→Layer2数据交接",
            "node_code": "collab_l1_l2",
            "layer_tag": "Layer1→2",
            "eval_layer": "L2 协作",
            "obj_metric_1_name": "可视化编译全通过率",
            "obj_metric_1_source": "Layer1编译success的card数/总数",
            "obj_metric_2_name": "数据引用完整性",
            "obj_metric_2_source": "report引用的viz URL数/Layer1输出URL数",
            "subj_metric_1_name": "Layer0→Layer1数据一致性",
            "subj_metric_1_method": "LLM初评（数据在Layer1可视化中是否准确反映，1-5分）",
            "obj_score_formula": "编译通过率*0.5 + 引用完整*0.5",
            "subj_score_formula": "一致性/5",
            "belongs_to": "协作层",
            "layer_weight": "Layer1权重30%",
            "node_weight_rule": "协作节点独立计算",
            "is_gate": True,
            "gate_type": "GateB",
            "gate_condition": "所有viz编译通过+引用完整",
            "sort_order": 51
        },
        
        # ========== L3 系统层 (1个节点) ==========
        {
            "agent_name": "系统层",
            "node_name": "Investigation端到端评估",
            "node_code": "system_e2e",
            "layer_tag": "全链路",
            "eval_layer": "L3 系统",
            "obj_metric_1_name": "各Milestone Gate通过率",
            "obj_metric_1_source": "通过Gate数/总Gate数",
            "obj_metric_2_name": "总工具调用次数",
            "obj_metric_2_source": "Langfuse全链路tool_call count",
            "obj_metric_3_name": "总耗时",
            "obj_metric_3_source": "Langfuse investigation duration",
            "subj_metric_1_name": "query回答率",
            "subj_metric_1_method": "LLM初评+人工复核（1-5分）",
            "subj_metric_2_name": "幻觉率",
            "subj_metric_2_method": "LLM初评+人工复核（幻觉断言占比）",
            "obj_score_formula": "Gate通过率*0.4 + 工具效率*0.3 + 耗时达标*0.3",
            "subj_score_formula": "(回答率 + (1-幻觉率)*5)/10",
            "belongs_to": "系统层",
            "layer_weight": "综合三层加权",
            "node_weight_rule": "Layer0*0.3+Layer1*0.3+Layer2*0.4",
            "is_gate": True,
            "gate_type": "GateC",
            "gate_condition": "报告完整+幻觉率<阈值+query回答率达标",
            "remark": "最终业务质量信号，触发人工flywheel",
            "sort_order": 60
        },
    ]
    
    for node_data in nodes_data:
        node = EvalNodeDefinition(**node_data)
        db.add(node)
    
    # 创建Gate定义
    gates_data = [
        {
            "gate_type": "Gate0",
            "name": "MainAgent输出Gate",
            "description": "MainAgent LLM调用后的质量关口",
            "trigger_point": "MainAgent LLM调用完成后",
            "source_layer": None,
            "target_layer": "Layer0",
            "pass_conditions": {
                "output_structure_valid": True,
                "plan_reasonable": True
            },
            "on_fail_action": "retry",
            "retry_limit": 3,
            "related_node_codes": ["main_llm_call"],
            "sort_order": 0
        },
        {
            "gate_type": "GateA",
            "name": "Layer0结束Gate",
            "description": "Layer0数据采集完成后的质量关口",
            "trigger_point": "所有SearchCard完成后",
            "source_layer": "Layer0",
            "target_layer": "Layer1",
            "pass_conditions": {
                "recall_coverage": 0.8,
                "evidence_complete": True
            },
            "on_fail_action": "retry",
            "retry_limit": 2,
            "related_node_codes": ["search_result_summary", "collab_l0_l1"],
            "sort_order": 1
        },
        {
            "gate_type": "GateB",
            "name": "Layer1结束Gate",
            "description": "Layer1可视化完成后的质量关口",
            "trigger_point": "所有VizCard编译完成后",
            "source_layer": "Layer1",
            "target_layer": "Layer2",
            "pass_conditions": {
                "all_compile_success": True,
                "data_reference_complete": True
            },
            "on_fail_action": "rollback",
            "retry_limit": 2,
            "related_node_codes": ["chart_compile_gate", "map_compile_gate", "network_compile_gate", "timeline_compile_gate", "collab_l1_l2"],
            "sort_order": 2
        },
        {
            "gate_type": "GateC",
            "name": "Layer2结束Gate",
            "description": "报告生成完成后的最终质量关口",
            "trigger_point": "报告编译上传完成后",
            "source_layer": "Layer2",
            "target_layer": None,
            "pass_conditions": {
                "report_complete": True,
                "hallucination_rate_below": 0.1,
                "query_answer_rate_above": 0.8
            },
            "on_fail_action": "manual_review",
            "retry_limit": 1,
            "related_node_codes": ["report_chapter_gate", "report_assemble", "report_final_compile", "system_e2e"],
            "sort_order": 3
        },
    ]
    
    for gate_data in gates_data:
        gate = GateDefinition(**gate_data)
        db.add(gate)
    
    await db.commit()
    
    return {
        "message": "评测节点初始化成功",
        "initialized": True,
        "nodes_count": len(nodes_data),
        "gates_count": len(gates_data)
    }
