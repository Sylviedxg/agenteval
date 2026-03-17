import random
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.experiment import Experiment, EvalPlan, ConfigSnapshot
from app.models.dataset import Dataset, Case
from app.models.trace import Trace, NodeResult
from app.models.product import Product
from app.models.metric import MetricDefinition, AgentType, AgentMetricMapping

router = APIRouter(prefix="/mock", tags=["mock"])

MOCK_RAW_TRACE = {
    "query": "分析特斯拉最新财报，找出关键风险因素",
    "final_answer": "特斯拉Q3财报显示营收同比增长8%，但毛利率下滑至17.9%，主要风险包括：价格战压力、中国市场竞争加剧、Cybertruck产能爬坡不及预期。",
    "total_latency_ms": 12500,
    "total_tokens": 8420,
    "nodes": [
        {
            "node_id": "main_agent_0",
            "node_name": "MainAgent",
            "node_type": "main_agent",
            "status": "success",
            "input_summary": "用户查询：分析特斯拉最新财报，找出关键风险因素",
            "output_summary": "已规划3个子任务：搜索财报数据、搜索新闻、生成分析报告",
            "latency_ms": 1200,
            "tokens_used": 820,
            "auto_scores": {},
            "manual_scores": {},
            "events": [
                {
                    "event_type": "llm_call",
                    "model": "gpt-4o",
                    "prompt_tokens": 450,
                    "completion_tokens": 370,
                    "latency_ms": 1100,
                    "input_summary": "系统Prompt + 用户查询 + 可用工具列表",
                    "output_summary": "规划TODO：1.搜索特斯拉Q3财报 2.搜索相关新闻 3.生成分析报告"
                },
                {
                    "event_type": "delegate",
                    "card_type": "SearchCard",
                    "card_id": "search_card_0",
                    "instruction": "搜索特斯拉2024年Q3季度财报数据，重点关注营收、毛利率、净利润指标",
                    "priority": 1
                },
                {
                    "event_type": "delegate",
                    "card_type": "SearchCard",
                    "card_id": "search_card_1",
                    "instruction": "搜索特斯拉近期负面新闻和风险事件",
                    "priority": 1
                },
                {
                    "event_type": "bubble",
                    "card_id": "search_card_0",
                    "finding_type": "KEY_EVIDENCE",
                    "content": "特斯拉Q3营收251亿美元，同比+8%；毛利率17.9%，同比-320bps；净利润21.7亿美元，同比-44%"
                },
                {
                    "event_type": "delegate",
                    "card_type": "ReportCard",
                    "card_id": "report_card_0",
                    "instruction": "基于搜集到的财报数据和新闻，生成风险分析报告",
                    "priority": 2
                }
            ]
        },
        {
            "node_id": "search_card_0",
            "node_name": "SearchCard",
            "node_type": "card_agent",
            "card_type": "SearchCard",
            "status": "success",
            "input_summary": "搜索特斯拉2024年Q3季度财报数据",
            "output_summary": "找到财报关键数据：营收251亿、毛利率17.9%、净利润21.7亿",
            "latency_ms": 3200,
            "tokens_used": 2100,
            "auto_scores": {"metric_search_relevance": 8.5},
            "manual_scores": {},
            "events": [
                {
                    "event_type": "tool_call",
                    "tool_name": "web_search",
                    "tool_input": {"query": "Tesla Q3 2024 earnings report revenue gross margin"},
                    "tool_output": {"results_count": 10, "top_result": "Tesla Q3 2024: Revenue $25.18B..."},
                    "latency_ms": 800
                },
                {
                    "event_type": "tool_call",
                    "tool_name": "web_fetch",
                    "tool_input": {"url": "https://ir.tesla.com/quarterly-results"},
                    "tool_output": {"content_length": 15420, "status": "success"},
                    "latency_ms": 1200
                },
                {
                    "event_type": "llm_call",
                    "model": "gpt-4o",
                    "prompt_tokens": 890,
                    "completion_tokens": 420,
                    "latency_ms": 980,
                    "input_summary": "财报原文内容 + 提取指令",
                    "output_summary": "提取结果：营收251亿(+8% YoY)，毛利率17.9%(-3.2pp)，净利润21.7亿(-44%)"
                },
                {
                    "event_type": "bubble",
                    "card_id": "search_card_0",
                    "finding_type": "KEY_EVIDENCE",
                    "content": "特斯拉Q3营收251亿美元，同比+8%；毛利率17.9%，同比-320bps；净利润21.7亿美元，同比-44%"
                }
            ]
        },
        {
            "node_id": "search_card_1",
            "node_name": "SearchCard（新闻）",
            "node_type": "card_agent",
            "card_type": "SearchCard",
            "status": "success",
            "input_summary": "搜索特斯拉近期负面新闻和风险事件",
            "output_summary": "发现3个主要风险：价格战、中国竞争、Cybertruck产能",
            "latency_ms": 2800,
            "tokens_used": 1900,
            "auto_scores": {"metric_search_relevance": 7.2},
            "manual_scores": {},
            "events": [
                {
                    "event_type": "tool_call",
                    "tool_name": "web_search",
                    "tool_input": {"query": "Tesla risks 2024 China competition price war"},
                    "tool_output": {"results_count": 10, "top_result": "Tesla faces intensifying competition..."},
                    "latency_ms": 750
                },
                {
                    "event_type": "bubble",
                    "card_id": "search_card_1",
                    "finding_type": "ACTION_SUGGESTION",
                    "content": "建议重点关注中国市场份额变化趋势，BYD已超越特斯拉成为Q3全球纯电销量第一"
                }
            ]
        },
        {
            "node_id": "report_card_0",
            "node_name": "ReportCard",
            "node_type": "card_agent",
            "card_type": "ReportCard",
            "status": "success",
            "input_summary": "基于搜集数据生成风险分析报告",
            "output_summary": "生成完整分析报告，识别出3大风险因素",
            "latency_ms": 4200,
            "tokens_used": 3200,
            "auto_scores": {},
            "manual_scores": {},
            "events": [
                {
                    "event_type": "llm_call",
                    "model": "gpt-4o",
                    "prompt_tokens": 2100,
                    "completion_tokens": 890,
                    "latency_ms": 3800,
                    "input_summary": "所有SearchCard的输出摘要 + 报告生成指令",
                    "output_summary": "风险分析报告：1.价格战压力 2.中国市场竞争 3.Cybertruck产能问题"
                }
            ]
        }
    ]
}


@router.post("/inject-trace")
async def inject_mock_trace(db: AsyncSession = Depends(get_db)):
    experiment_result = await db.execute(
        select(Experiment).order_by(Experiment.created_at.desc()).limit(1)
    )
    experiment = experiment_result.scalar_one_or_none()
    
    if not experiment:
        return {"error": "No experiment found. Please create an experiment first."}
    
    case_result = await db.execute(
        select(Case).limit(1)
    )
    case = case_result.scalar_one_or_none()
    
    if not case:
        dataset_result = await db.execute(
            select(Dataset).limit(1)
        )
        dataset = dataset_result.scalar_one_or_none()
        
        if not dataset:
            dataset = Dataset(name="Mock Dataset", version="1.0.0")
            db.add(dataset)
            await db.flush()
        
        case = Case(
            dataset_id=dataset.id,
            title="Mock Case - 特斯拉财报分析",
            input_query="分析特斯拉最新财报，找出关键风险因素"
        )
        db.add(case)
        await db.flush()
    
    trace = Trace(
        experiment_id=experiment.id,
        case_id=case.id,
        status="completed",
        raw_trace=MOCK_RAW_TRACE,
        total_tokens=MOCK_RAW_TRACE["total_tokens"],
        total_latency_ms=MOCK_RAW_TRACE["total_latency_ms"]
    )
    db.add(trace)
    await db.flush()
    await db.refresh(trace)
    
    return {"trace_id": str(trace.id), "message": "Mock trace injected successfully"}


@router.post("/create-full-experiment")
async def create_full_mock_experiment(db: AsyncSession = Depends(get_db)):
    """创建完整的 Mock 评测实验，包括产品、数据集、评测计划、实验、Trace 和指标评分"""
    
    # 1. 创建或获取产品
    product_result = await db.execute(
        select(Product).where(Product.name == "TanQi AI Agent")
    )
    product = product_result.scalar_one_or_none()
    if not product:
        product = Product(
            name="TanQi AI Agent",
            description="TanQi 智能调研助手",
            version="2.0.0"
        )
        db.add(product)
        await db.flush()
    
    # 2. 创建配置快照
    config_snapshot = ConfigSnapshot(
        product_id=product.id,
        snapshot_name="v2.0.0-20240317",
        model_config={
            "main_agent": "gpt-4o",
            "card_agents": "gpt-4o-mini",
            "temperature": 0.7
        },
        prompt_versions={
            "main_agent_system": "v1.2.0",
            "search_card_system": "v1.1.0",
            "report_card_system": "v1.3.0"
        }
    )
    db.add(config_snapshot)
    await db.flush()
    
    # 3. 创建数据集和测试用例
    dataset = Dataset(
        name="TanQi 评测数据集 v1",
        description="包含金融分析、市场调研等场景的测试用例",
        version="1.0.0"
    )
    db.add(dataset)
    await db.flush()
    
    cases_data = [
        {"title": "特斯拉财报分析", "input_query": "分析特斯拉最新财报，找出关键风险因素"},
        {"title": "比亚迪市场调研", "input_query": "分析比亚迪2024年销量数据和市场份额变化"},
        {"title": "AI芯片竞争格局", "input_query": "分析英伟达、AMD、Intel在AI芯片市场的竞争格局"},
    ]
    cases = []
    for case_data in cases_data:
        case = Case(dataset_id=dataset.id, **case_data)
        db.add(case)
        cases.append(case)
    await db.flush()
    
    # 4. 创建评测计划
    # 获取所有指标
    metrics_result = await db.execute(select(MetricDefinition).where(MetricDefinition.is_active == True))
    metrics = metrics_result.scalars().all()
    metric_ids = [str(m.id) for m in metrics]
    
    eval_plan = EvalPlan(
        name="TanQi Agent 全面评测",
        description="覆盖系统层、协作层、单体层的完整评测计划",
        metric_ids=metric_ids,
        node_metric_mapping={
            "main_agent": ["plan_quality", "parallel_efficiency", "delegate_success_rate"],
            "search_card": ["tool_call_success_rate", "tool_selection_accuracy", "response_relevance"],
            "report_card": ["task_completion", "info_completeness", "output_accuracy"]
        }
    )
    db.add(eval_plan)
    await db.flush()
    
    # 5. 创建实验
    experiment = Experiment(
        name=f"TanQi Agent 评测 - {cases_data[0]['title']}",
        product_id=product.id,
        dataset_id=dataset.id,
        config_snapshot_id=config_snapshot.id,
        eval_plan_id=eval_plan.id,
        status="completed",
        total_cases=len(cases),
        completed_cases=len(cases),
        overall_score=7.8
    )
    db.add(experiment)
    await db.flush()
    
    # 6. 为每个用例创建 Trace 和 NodeResult
    traces_created = []
    for i, case in enumerate(cases):
        # 创建 Trace
        trace = Trace(
            experiment_id=experiment.id,
            case_id=case.id,
            status="completed",
            raw_trace=MOCK_RAW_TRACE,
            total_tokens=MOCK_RAW_TRACE["total_tokens"] + random.randint(-500, 500),
            total_latency_ms=MOCK_RAW_TRACE["total_latency_ms"] + random.randint(-1000, 2000)
        )
        db.add(trace)
        await db.flush()
        traces_created.append(trace)
        
        # 为每个节点创建 NodeResult
        for node in MOCK_RAW_TRACE["nodes"]:
            node_type = node.get("card_type", node.get("node_type", "unknown")).lower()
            if node_type == "searchcard":
                node_type = "search_card"
            elif node_type == "reportcard":
                node_type = "report_card"
            
            # 生成模拟的指标评分
            auto_scores = {
                "tool_call_success_rate": round(random.uniform(0.85, 1.0), 2),
                "tool_selection_accuracy": round(random.uniform(0.80, 0.95), 2),
            }
            manual_scores = {
                "response_relevance": round(random.uniform(7.0, 9.5), 1),
                "info_completeness": round(random.uniform(6.5, 9.0), 1),
                "output_accuracy": round(random.uniform(7.0, 9.0), 1),
            }
            
            if node_type == "main_agent":
                auto_scores["parallel_efficiency"] = round(random.uniform(0.6, 0.9), 2)
                manual_scores["plan_quality"] = round(random.uniform(7.0, 9.0), 1)
                manual_scores["delegate_success_rate"] = round(random.uniform(0.85, 1.0), 2)
            elif node_type == "report_card":
                manual_scores["task_completion"] = round(random.uniform(7.5, 9.5), 1)
                auto_scores["code_execution_success"] = round(random.uniform(0.9, 1.0), 2)
            
            node_result = NodeResult(
                trace_id=trace.id,
                node_name=node["node_name"],
                node_type=node_type,
                metric_scores={**auto_scores, **manual_scores},
                auto_scores=auto_scores,
                manual_scores=manual_scores,
                node_input={"summary": node.get("input_summary", "")},
                node_output={"summary": node.get("output_summary", "")},
                latency_ms=node.get("latency_ms", 0) + random.randint(-100, 200),
                tokens_used=node.get("tokens_used", 0) + random.randint(-50, 100)
            )
            db.add(node_result)
    
    await db.commit()
    
    return {
        "message": "完整 Mock 评测实验创建成功",
        "experiment_id": str(experiment.id),
        "product_id": str(product.id),
        "dataset_id": str(dataset.id),
        "eval_plan_id": str(eval_plan.id),
        "traces_count": len(traces_created),
        "cases_count": len(cases)
    }


@router.get("/experiment-summary/{experiment_id}")
async def get_experiment_summary(experiment_id: str, db: AsyncSession = Depends(get_db)):
    """获取实验评测结果摘要"""
    import uuid
    
    # 获取实验
    exp_result = await db.execute(
        select(Experiment).where(Experiment.id == uuid.UUID(experiment_id))
    )
    experiment = exp_result.scalar_one_or_none()
    if not experiment:
        return {"error": "Experiment not found"}
    
    # 获取所有 Trace
    traces_result = await db.execute(
        select(Trace).where(Trace.experiment_id == experiment.id)
    )
    traces = traces_result.scalars().all()
    
    # 获取所有 NodeResult
    all_node_results = []
    for trace in traces:
        nodes_result = await db.execute(
            select(NodeResult).where(NodeResult.trace_id == trace.id)
        )
        all_node_results.extend(nodes_result.scalars().all())
    
    # 按节点类型聚合指标
    node_type_metrics = {}
    for nr in all_node_results:
        nt = nr.node_type or "unknown"
        if nt not in node_type_metrics:
            node_type_metrics[nt] = {"count": 0, "metrics": {}}
        node_type_metrics[nt]["count"] += 1
        
        if nr.metric_scores:
            for metric, score in nr.metric_scores.items():
                if metric not in node_type_metrics[nt]["metrics"]:
                    node_type_metrics[nt]["metrics"][metric] = []
                node_type_metrics[nt]["metrics"][metric].append(score)
    
    # 计算平均值
    for nt, data in node_type_metrics.items():
        for metric, scores in data["metrics"].items():
            data["metrics"][metric] = {
                "avg": round(sum(scores) / len(scores), 2),
                "min": round(min(scores), 2),
                "max": round(max(scores), 2),
                "count": len(scores)
            }
    
    # 计算整体指标
    overall_metrics = {}
    for nr in all_node_results:
        if nr.metric_scores:
            for metric, score in nr.metric_scores.items():
                if metric not in overall_metrics:
                    overall_metrics[metric] = []
                overall_metrics[metric].append(score)
    
    for metric, scores in overall_metrics.items():
        overall_metrics[metric] = {
            "avg": round(sum(scores) / len(scores), 2),
            "min": round(min(scores), 2),
            "max": round(max(scores), 2),
            "count": len(scores)
        }
    
    return {
        "experiment": {
            "id": str(experiment.id),
            "name": experiment.name,
            "status": experiment.status,
            "total_cases": experiment.total_cases,
            "completed_cases": experiment.completed_cases,
            "overall_score": experiment.overall_score
        },
        "traces_count": len(traces),
        "node_results_count": len(all_node_results),
        "metrics_by_node_type": node_type_metrics,
        "overall_metrics": overall_metrics
    }
