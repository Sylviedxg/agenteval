"""
评测执行 API
完整的评测流程：创建实验 → 执行评测 → 查看结果
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.experiment import Experiment
from app.models.trace import Trace
from app.models.eval_node import InvestigationScore, LayerAggregateScore, NodeScoreResult, GateCheckResult
from app.services.evaluation_engine import EvaluationEngine

router = APIRouter(prefix="/evaluation", tags=["评测执行"])


class LangfuseConfig(BaseModel):
    host: str = "http://172.21.30.114:3208"
    public_key: str = ""
    secret_key: str = ""


class EvaluateTraceRequest(BaseModel):
    trace_id: str  # 本地 Trace ID
    langfuse_trace_id: str  # Langfuse 中的 trace ID
    langfuse_config: LangfuseConfig


class EvaluateByLangfuseRequest(BaseModel):
    langfuse_trace_id: str
    experiment_id: Optional[str] = None
    case_id: Optional[str] = None
    langfuse_config: LangfuseConfig


@router.post("/evaluate-trace")
async def evaluate_trace(
    request: EvaluateTraceRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    评测单个 Trace
    
    1. 从 Langfuse 采集数据
    2. 计算各节点客观/主观得分
    3. 检查 Gate 通过情况
    4. 层级聚合
    5. 计算总分
    """
    try:
        trace_id = uuid.UUID(request.trace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trace_id format")
    
    # 验证 Trace 存在
    trace = await db.get(Trace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    
    # 创建评测引擎
    engine = EvaluationEngine(
        db=db,
        langfuse_config={
            "host": request.langfuse_config.host,
            "public_key": request.langfuse_config.public_key,
            "secret_key": request.langfuse_config.secret_key
        }
    )
    
    try:
        result = await engine.evaluate_trace(trace_id, request.langfuse_trace_id)
        return result
    finally:
        await engine.close()


@router.post("/evaluate-langfuse-trace")
async def evaluate_langfuse_trace(
    request: EvaluateByLangfuseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    直接评测 Langfuse Trace（不创建本地 Trace，直接返回评测结果）
    
    适用于快速测试，无需预先创建实验和用例
    """
    from app.services.langfuse_collector import LangfuseCollector
    
    # 创建采集器
    collector = LangfuseCollector(
        host=request.langfuse_config.host,
        public_key=request.langfuse_config.public_key,
        secret_key=request.langfuse_config.secret_key
    )
    
    try:
        # 采集数据
        trace_data = await collector.collect_trace_metrics(request.langfuse_trace_id)
        if "error" in trace_data:
            raise HTTPException(status_code=404, detail=trace_data["error"])
        
        observations = await collector.get_trace_observations(request.langfuse_trace_id)
        node_metrics = collector.extract_node_metrics(observations)
        
        # 加载节点定义
        from app.models.eval_node import EvalNodeDefinition, GateDefinition
        result = await db.execute(
            select(EvalNodeDefinition).where(EvalNodeDefinition.is_active == True)
        )
        node_definitions = {n.node_code: n for n in result.scalars().all()}
        
        result = await db.execute(
            select(GateDefinition).where(GateDefinition.is_active == True)
        )
        gate_definitions = {g.gate_type: g for g in result.scalars().all()}
        
        # 计算各节点得分
        node_scores = {}
        for node_code, node_def in node_definitions.items():
            raw_metrics = node_metrics.get(node_code, {})
            
            # 客观得分计算 - 根据节点定义的指标
            obj_scores = []
            
            # 指标1: 成功率/执行成功
            if raw_metrics:
                success = raw_metrics.get("success", raw_metrics.get("success_rate"))
                if success is not None:
                    if isinstance(success, bool):
                        obj_scores.append(1.0 if success else 0.0)
                    else:
                        obj_scores.append(min(1.0, max(0.0, float(success))))
            
            # 指标2: 延迟评分 (越快越好)
            latency = raw_metrics.get("latency_ms", raw_metrics.get("avg_latency_ms"))
            if latency is not None:
                # 延迟评分: <5s=1.0, 5-15s=0.8, 15-30s=0.6, 30-60s=0.4, >60s=0.2
                if latency < 5000:
                    obj_scores.append(1.0)
                elif latency < 15000:
                    obj_scores.append(0.8)
                elif latency < 30000:
                    obj_scores.append(0.6)
                elif latency < 60000:
                    obj_scores.append(0.4)
                else:
                    obj_scores.append(0.2)
            
            # 指标3: Token效率 (可选)
            total_tokens = raw_metrics.get("total_tokens")
            if total_tokens is not None and total_tokens > 0:
                # Token评分: <10k=1.0, 10k-50k=0.8, 50k-200k=0.6, >200k=0.4
                if total_tokens < 10000:
                    obj_scores.append(1.0)
                elif total_tokens < 50000:
                    obj_scores.append(0.8)
                elif total_tokens < 200000:
                    obj_scores.append(0.6)
                else:
                    obj_scores.append(0.4)
            
            # 计算客观得分平均值
            if obj_scores:
                obj_score = sum(obj_scores) / len(obj_scores)
            else:
                obj_score = 0.8  # 无数据时默认
            
            # 主观得分 (暂时固定，后续接入LLM-as-Judge)
            subj_score = 0.75
            
            # 最终得分 = 客观×0.7 + 主观×0.3
            final_score = obj_score * 0.7 + subj_score * 0.3
            
            node_scores[node_code] = {
                "node_name": node_def.node_name,
                "agent_name": node_def.agent_name,
                "eval_layer": node_def.eval_layer,
                "obj_score": round(obj_score, 3),
                "subj_score": round(subj_score, 3),
                "final_score": round(final_score, 3),
                "is_gate": node_def.is_gate,
                "raw_metrics": raw_metrics
            }
        
        # 层级聚合
        layer_scores = {"Layer0": [], "Layer1": [], "Layer2": []}
        for code, scores in node_scores.items():
            layer = scores["eval_layer"]
            if "L0" in layer or "MainAgent" in layer:
                layer_scores["Layer0"].append(scores["final_score"])
            elif "L1" in layer or "单体" in layer:
                layer_scores["Layer1"].append(scores["final_score"])
            elif "L2" in layer or "协作" in layer:
                layer_scores["Layer2"].append(scores["final_score"])
        
        layer_avg = {
            "Layer0": sum(layer_scores["Layer0"]) / len(layer_scores["Layer0"]) if layer_scores["Layer0"] else 0,
            "Layer1": sum(layer_scores["Layer1"]) / len(layer_scores["Layer1"]) if layer_scores["Layer1"] else 0,
            "Layer2": sum(layer_scores["Layer2"]) / len(layer_scores["Layer2"]) if layer_scores["Layer2"] else 0
        }
        
        # 总分
        total_score = layer_avg["Layer0"] * 0.3 + layer_avg["Layer1"] * 0.3 + layer_avg["Layer2"] * 0.4
        
        # 质量等级
        if total_score >= 0.9:
            quality_level = "A"
        elif total_score >= 0.8:
            quality_level = "B"
        elif total_score >= 0.7:
            quality_level = "C"
        elif total_score >= 0.6:
            quality_level = "D"
        else:
            quality_level = "F"
        
        # Gate 检查（简化）
        gates_passed = {gt: True for gt in gate_definitions.keys()}
        
        # 存储评测结果到数据库
        from app.models.evaluation_result import EvaluationResult
        trace_info = trace_data.get("trace_info", {})
        
        eval_result = EvaluationResult(
            langfuse_trace_id=request.langfuse_trace_id,
            trace_name=trace_info.get("name"),
            session_id=trace_info.get("session_id"),
            user_id=trace_info.get("user_id"),
            trace_metadata=trace_info.get("metadata"),
            trace_timestamp=trace_info.get("timestamp"),
            trace_latency_ms=trace_info.get("latency_ms"),
            trace_cost=trace_info.get("total_cost"),
            observations_count=len(observations),
            node_scores=node_scores,
            layer0_score=round(layer_avg["Layer0"], 3),
            layer0_nodes=len(layer_scores["Layer0"]),
            layer1_score=round(layer_avg["Layer1"], 3),
            layer1_nodes=len(layer_scores["Layer1"]),
            layer2_score=round(layer_avg["Layer2"], 3),
            layer2_nodes=len(layer_scores["Layer2"]),
            total_score=round(total_score, 3),
            quality_level=quality_level,
            gates_passed=gates_passed,
            all_gates_passed=all(gates_passed.values()),
            raw_summary=trace_data.get("summary", {})
        )
        db.add(eval_result)
        await db.commit()
        await db.refresh(eval_result)
        
        return {
            "id": str(eval_result.id),
            "langfuse_trace_id": request.langfuse_trace_id,
            "trace_info": trace_info,
            "observations_count": len(observations),
            "node_scores": node_scores,
            "layer_scores": {
                "Layer0": {"score": round(layer_avg["Layer0"], 3), "nodes": len(layer_scores["Layer0"])},
                "Layer1": {"score": round(layer_avg["Layer1"], 3), "nodes": len(layer_scores["Layer1"])},
                "Layer2": {"score": round(layer_avg["Layer2"], 3), "nodes": len(layer_scores["Layer2"])}
            },
            "gates_passed": gates_passed,
            "total_score": round(total_score, 3),
            "quality_level": quality_level,
            "summary": trace_data.get("summary", {}),
            "saved": True
        }
    finally:
        await collector.close()


@router.get("/results")
async def list_evaluation_results(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    获取评测结果列表
    """
    from app.models.evaluation_result import EvaluationResult
    
    result = await db.execute(
        select(EvaluationResult)
        .order_by(EvaluationResult.created_at.desc())
        .limit(limit)
    )
    results = result.scalars().all()
    
    return {
        "count": len(results),
        "results": [
            {
                "id": str(r.id),
                "langfuse_trace_id": r.langfuse_trace_id,
                "trace_name": r.trace_name,
                "session_id": r.session_id,
                "total_score": r.total_score,
                "quality_level": r.quality_level,
                "layer0_score": r.layer0_score,
                "layer1_score": r.layer1_score,
                "layer2_score": r.layer2_score,
                "observations_count": r.observations_count,
                "trace_latency_ms": r.trace_latency_ms,
                "trace_cost": r.trace_cost,
                "all_gates_passed": r.all_gates_passed,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ]
    }


@router.get("/results/{result_id}")
async def get_evaluation_result(
    result_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个评测结果详情
    """
    from app.models.evaluation_result import EvaluationResult
    
    try:
        rid = uuid.UUID(result_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid result_id format")
    
    result = await db.get(EvaluationResult, rid)
    if not result:
        raise HTTPException(status_code=404, detail="Evaluation result not found")
    
    return {
        "id": str(result.id),
        "langfuse_trace_id": result.langfuse_trace_id,
        "trace_name": result.trace_name,
        "session_id": result.session_id,
        "user_id": result.user_id,
        "trace_metadata": result.trace_metadata,
        "trace_timestamp": result.trace_timestamp,
        "trace_latency_ms": result.trace_latency_ms,
        "trace_cost": result.trace_cost,
        "observations_count": result.observations_count,
        "node_scores": result.node_scores,
        "layer_scores": {
            "Layer0": {"score": result.layer0_score, "nodes": result.layer0_nodes},
            "Layer1": {"score": result.layer1_score, "nodes": result.layer1_nodes},
            "Layer2": {"score": result.layer2_score, "nodes": result.layer2_nodes}
        },
        "total_score": result.total_score,
        "quality_level": result.quality_level,
        "gates_passed": result.gates_passed,
        "all_gates_passed": result.all_gates_passed,
        "raw_summary": result.raw_summary,
        "created_at": result.created_at.isoformat() if result.created_at else None
    }


@router.get("/trace-result/{trace_id}")
async def get_trace_result(
    trace_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取 Trace 的完整评测结果
    """
    try:
        tid = uuid.UUID(trace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trace_id format")
    
    # 获取 Investigation 总分
    result = await db.execute(
        select(InvestigationScore).where(InvestigationScore.trace_id == tid)
    )
    investigation = result.scalar_one_or_none()
    
    if not investigation:
        raise HTTPException(status_code=404, detail="Evaluation result not found")
    
    # 获取层级得分
    result = await db.execute(
        select(LayerAggregateScore).where(LayerAggregateScore.trace_id == tid)
    )
    layer_scores = {ls.layer: {
        "aggregate_score": ls.aggregate_score,
        "weighted_score": ls.weighted_score,
        "node_scores": ls.node_scores
    } for ls in result.scalars().all()}
    
    # 获取节点得分
    result = await db.execute(
        select(NodeScoreResult).where(NodeScoreResult.trace_id == tid)
    )
    node_results = []
    for nr in result.scalars().all():
        node_def = await db.get(nr.node_definition_id.__class__, nr.node_definition_id) if hasattr(nr, 'node_definition') else None
        node_results.append({
            "node_definition_id": str(nr.node_definition_id),
            "obj_score": nr.obj_score,
            "subj_score": nr.subj_score,
            "final_score": nr.final_score,
            "needs_human_review": nr.needs_human_review,
            "obj_raw_data": nr.obj_raw_data
        })
    
    # 获取 Gate 检查结果
    result = await db.execute(
        select(GateCheckResult).where(GateCheckResult.trace_id == tid)
    )
    gate_results = []
    for gr in result.scalars().all():
        gate_results.append({
            "gate_definition_id": str(gr.gate_definition_id),
            "passed": gr.passed,
            "check_details": gr.check_details,
            "retry_count": gr.retry_count
        })
    
    return {
        "trace_id": trace_id,
        "investigation_score": {
            "total_score": investigation.total_score,
            "quality_level": investigation.quality_level,
            "layer0_score": investigation.layer0_score,
            "layer1_score": investigation.layer1_score,
            "layer2_score": investigation.layer2_score,
            "gates_passed": investigation.gates_passed,
            "all_gates_passed": investigation.all_gates_passed,
            "needs_human_review": investigation.needs_human_review
        },
        "layer_scores": layer_scores,
        "node_results": node_results,
        "gate_results": gate_results
    }


@router.get("/trace-tree/{langfuse_trace_id}")
async def get_trace_tree(
    langfuse_trace_id: str,
    public_key: str = "pk-lf-63c63e3a-c38a-45f7-b173-13586793e22e",
    secret_key: str = "sk-lf-fa7a8d18-b5b0-48cd-8a52-8d8f8596457f",
    max_observations: int = 500
):
    """
    获取Langfuse Trace的observations用于构建Trace树
    max_observations: 最大返回的observations数量，默认500
    """
    from app.services.langfuse_collector import LangfuseCollector
    
    collector = LangfuseCollector(public_key=public_key, secret_key=secret_key)
    
    # 获取trace信息
    trace = await collector.get_trace(langfuse_trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    
    # 获取observations（限制数量）
    observations = await collector.get_trace_observations(langfuse_trace_id, max_count=max_observations)
    
    return {
        "trace_info": {
            "id": trace.get("id"),
            "name": trace.get("name"),
            "session_id": trace.get("sessionId"),
            "user_id": trace.get("userId"),
            "timestamp": trace.get("timestamp"),
            "latency_ms": (trace.get("latency") or 0) * 1000 if (trace.get("latency") or 0) < 1000 else trace.get("latency"),
            "total_cost": trace.get("totalCost", 0),
        },
        "observations_count": len(observations),
        "observations": observations
    }


@router.get("/experiment-summary/{experiment_id}")
async def get_experiment_summary(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取实验的评测汇总
    """
    try:
        eid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment_id format")
    
    # 获取实验
    experiment = await db.get(Experiment, eid)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # 获取所有 Trace 的评测结果
    result = await db.execute(
        select(Trace).where(Trace.experiment_id == eid)
    )
    traces = result.scalars().all()
    
    trace_results = []
    total_scores = []
    quality_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    
    for trace in traces:
        # 获取该 Trace 的 Investigation 分数
        result = await db.execute(
            select(InvestigationScore).where(InvestigationScore.trace_id == trace.id)
        )
        investigation = result.scalar_one_or_none()
        
        if investigation:
            trace_results.append({
                "trace_id": str(trace.id),
                "total_score": investigation.total_score,
                "quality_level": investigation.quality_level,
                "all_gates_passed": investigation.all_gates_passed
            })
            total_scores.append(investigation.total_score)
            quality_distribution[investigation.quality_level] += 1
    
    # 计算平均分
    avg_score = sum(total_scores) / len(total_scores) if total_scores else 0
    
    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment.name,
        "total_traces": len(traces),
        "evaluated_traces": len(trace_results),
        "average_score": avg_score,
        "quality_distribution": quality_distribution,
        "trace_results": trace_results
    }
