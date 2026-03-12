from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.experiment import Experiment
from app.models.dataset import Dataset, Case
from app.models.trace import Trace

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
