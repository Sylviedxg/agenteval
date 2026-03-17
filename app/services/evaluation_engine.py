"""
评测执行引擎
完整的评测流程：Langfuse数据采集 → 客观评分 → 主观评分 → 层级聚合 → 总分计算
"""
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.trace import Trace
from app.models.eval_node import (
    EvalNodeDefinition, GateDefinition, NodeScoreResult,
    GateCheckResult, LayerAggregateScore, InvestigationScore
)
from app.services.langfuse_collector import LangfuseCollector


class EvaluationEngine:
    """评测执行引擎"""
    
    # 层级权重
    LAYER_WEIGHTS = {
        "Layer0": 0.3,
        "Layer1": 0.3,
        "Layer2": 0.4
    }
    
    # 质量等级阈值
    QUALITY_LEVELS = [
        (0.9, "A"),
        (0.8, "B"),
        (0.7, "C"),
        (0.6, "D"),
        (0.0, "F")
    ]
    
    def __init__(self, db: AsyncSession, langfuse_config: Dict[str, str]):
        self.db = db
        self.collector = LangfuseCollector(
            host=langfuse_config.get("host", "http://172.21.30.114:3208"),
            public_key=langfuse_config.get("public_key", ""),
            secret_key=langfuse_config.get("secret_key", "")
        )
        self._node_definitions: Dict[str, EvalNodeDefinition] = {}
        self._gate_definitions: Dict[str, GateDefinition] = {}
    
    async def load_definitions(self):
        """加载节点和Gate定义"""
        # 加载节点定义
        result = await self.db.execute(
            select(EvalNodeDefinition).where(EvalNodeDefinition.is_active == True)
        )
        for node in result.scalars().all():
            self._node_definitions[node.node_code] = node
        
        # 加载Gate定义
        result = await self.db.execute(
            select(GateDefinition).where(GateDefinition.is_active == True)
        )
        for gate in result.scalars().all():
            self._gate_definitions[gate.gate_type] = gate
    
    async def evaluate_trace(self, trace_id: uuid.UUID, langfuse_trace_id: str) -> Dict[str, Any]:
        """
        评测单个 Trace
        
        Args:
            trace_id: 本地 Trace ID
            langfuse_trace_id: Langfuse 中的 trace ID
        
        Returns:
            评测结果摘要
        """
        await self.load_definitions()
        
        # 1. 从 Langfuse 采集数据
        trace_data = await self.collector.collect_trace_metrics(langfuse_trace_id)
        if "error" in trace_data:
            return {"error": trace_data["error"]}
        
        observations = await self.collector.get_trace_observations(langfuse_trace_id)
        node_metrics = self.collector.extract_node_metrics(observations)
        
        # 2. 计算各节点得分
        node_scores = await self._calculate_node_scores(trace_id, node_metrics, observations)
        
        # 3. 检查 Gate
        gate_results = await self._check_gates(trace_id, node_metrics, observations)
        
        # 4. 层级聚合
        layer_scores = await self._aggregate_layer_scores(trace_id, node_scores)
        
        # 5. 计算总分
        investigation_score = await self._calculate_investigation_score(
            trace_id, layer_scores, gate_results
        )
        
        # 6. 更新 Trace 状态
        trace = await self.db.get(Trace, trace_id)
        if trace:
            trace.status = "evaluated"
            trace.raw_trace = trace_data.get("trace_info", {})
            trace.total_tokens = trace_data.get("summary", {}).get("total_tokens", 0)
            trace.total_latency_ms = int(trace_data.get("summary", {}).get("total_latency_ms", 0))
        
        await self.db.commit()
        
        return {
            "trace_id": str(trace_id),
            "langfuse_trace_id": langfuse_trace_id,
            "node_scores": {k: v.get("final_score") for k, v in node_scores.items()},
            "layer_scores": layer_scores,
            "gates_passed": {k: v["passed"] for k, v in gate_results.items()},
            "total_score": investigation_score["total_score"],
            "quality_level": investigation_score["quality_level"],
            "needs_human_review": investigation_score["needs_human_review"]
        }
    
    async def _calculate_node_scores(
        self, 
        trace_id: uuid.UUID, 
        node_metrics: Dict[str, Dict],
        observations: List[Dict]
    ) -> Dict[str, Dict]:
        """计算各节点得分"""
        node_scores = {}
        
        for node_code, node_def in self._node_definitions.items():
            # 获取该节点的原始指标
            raw_metrics = node_metrics.get(node_code, {})
            
            # 从 observations 中提取更多数据
            obs_data = self._extract_node_observations(node_def, observations)
            
            # 计算客观得分
            obj_score, obj_values = self._calculate_objective_score(node_def, raw_metrics, obs_data)
            
            # 计算主观得分（暂时用默认值，后续接入 LLM-as-Judge）
            subj_score, needs_review = self._calculate_subjective_score(node_def, obs_data)
            
            # 最终得分
            final_score = obj_score * 0.7 + subj_score * 0.3 if obj_score is not None and subj_score is not None else None
            
            # 保存到数据库
            node_result = NodeScoreResult(
                trace_id=trace_id,
                node_definition_id=node_def.id,
                obj_metric_1_value=obj_values.get("metric_1"),
                obj_metric_2_value=obj_values.get("metric_2"),
                obj_metric_3_value=obj_values.get("metric_3"),
                obj_raw_data=raw_metrics,
                obj_score=obj_score,
                subj_score=subj_score,
                final_score=final_score,
                needs_human_review=needs_review
            )
            self.db.add(node_result)
            
            node_scores[node_code] = {
                "obj_score": obj_score,
                "subj_score": subj_score,
                "final_score": final_score,
                "needs_review": needs_review,
                "is_gate": node_def.is_gate,
                "gate_type": node_def.gate_type,
                "eval_layer": node_def.eval_layer
            }
        
        return node_scores
    
    def _extract_node_observations(
        self, 
        node_def: EvalNodeDefinition, 
        observations: List[Dict]
    ) -> Dict:
        """从 observations 中提取节点相关数据"""
        result = {"observations": [], "llm_calls": [], "tool_calls": []}
        
        agent_name = node_def.agent_name
        node_name = node_def.node_name
        
        for obs in observations:
            obs_name = obs.get("name", "")
            metadata = obs.get("metadata", {}) or {}
            
            # 匹配 agent
            if agent_name in obs_name or metadata.get("agent_name") == agent_name:
                result["observations"].append(obs)
                
                if obs.get("type") == "GENERATION":
                    result["llm_calls"].append(obs)
                elif obs.get("type") == "SPAN" and any(t in obs_name for t in ["web_search", "browse_url", "e2b_"]):
                    result["tool_calls"].append(obs)
        
        return result
    
    def _calculate_objective_score(
        self, 
        node_def: EvalNodeDefinition, 
        raw_metrics: Dict,
        obs_data: Dict
    ) -> tuple:
        """计算客观得分"""
        values = {}
        scores = []
        
        # 指标1
        if node_def.obj_metric_1_name:
            value = self._get_metric_value(node_def.obj_metric_1_name, node_def.obj_metric_1_source, raw_metrics, obs_data)
            values["metric_1"] = value
            if value is not None:
                scores.append(self._normalize_metric(node_def.obj_metric_1_name, value))
        
        # 指标2
        if node_def.obj_metric_2_name:
            value = self._get_metric_value(node_def.obj_metric_2_name, node_def.obj_metric_2_source, raw_metrics, obs_data)
            values["metric_2"] = value
            if value is not None:
                scores.append(self._normalize_metric(node_def.obj_metric_2_name, value))
        
        # 指标3
        if node_def.obj_metric_3_name:
            value = self._get_metric_value(node_def.obj_metric_3_name, node_def.obj_metric_3_source, raw_metrics, obs_data)
            values["metric_3"] = value
            if value is not None:
                scores.append(self._normalize_metric(node_def.obj_metric_3_name, value))
        
        # 平均得分
        obj_score = sum(scores) / len(scores) if scores else None
        return obj_score, values
    
    def _get_metric_value(
        self, 
        metric_name: str, 
        metric_source: str, 
        raw_metrics: Dict,
        obs_data: Dict
    ) -> Optional[float]:
        """获取指标值"""
        # 从 raw_metrics 中查找
        if "成功率" in metric_name:
            return raw_metrics.get("success_rate", raw_metrics.get("success", 1.0 if raw_metrics else None))
        if "延迟" in metric_name or "耗时" in metric_name:
            return raw_metrics.get("latency_ms", raw_metrics.get("avg_latency_ms"))
        if "token" in metric_name.lower():
            return raw_metrics.get("total_tokens")
        if "次数" in metric_name or "调用" in metric_name:
            return raw_metrics.get("total_calls", len(obs_data.get("observations", [])))
        
        # 从 observations 统计
        observations = obs_data.get("observations", [])
        if observations:
            if "成功" in metric_name:
                success_count = sum(1 for o in observations if o.get("level") != "ERROR")
                return success_count / len(observations) if observations else None
        
        return None
    
    def _normalize_metric(self, metric_name: str, value: float) -> float:
        """归一化指标值到 0-1"""
        if value is None:
            return 0.5  # 默认中间值
        
        # 成功率类指标，已经是 0-1
        if "成功率" in metric_name or "率" in metric_name:
            return min(1.0, max(0.0, value))
        
        # 延迟类指标，越小越好
        if "延迟" in metric_name or "耗时" in metric_name:
            # 假设 5000ms 以下为满分，30000ms 以上为 0 分
            if value <= 5000:
                return 1.0
            elif value >= 30000:
                return 0.0
            else:
                return 1.0 - (value - 5000) / 25000
        
        # 其他指标，假设是正向的
        return min(1.0, max(0.0, value))
    
    def _calculate_subjective_score(
        self, 
        node_def: EvalNodeDefinition, 
        obs_data: Dict
    ) -> tuple:
        """计算主观得分（暂时返回默认值）"""
        # TODO: 接入 LLM-as-Judge
        # 暂时根据客观数据给一个估计分
        observations = obs_data.get("observations", [])
        
        if not observations:
            return 0.7, False  # 无数据，给中等分
        
        # 简单估计：无错误给高分
        error_count = sum(1 for o in observations if o.get("level") == "ERROR")
        if error_count == 0:
            return 0.85, False
        elif error_count / len(observations) < 0.1:
            return 0.7, False
        else:
            return 0.5, True  # 错误多，需要人工复核
    
    async def _check_gates(
        self, 
        trace_id: uuid.UUID, 
        node_metrics: Dict,
        observations: List[Dict]
    ) -> Dict[str, Dict]:
        """检查 Gate 通过情况"""
        gate_results = {}
        
        for gate_type, gate_def in self._gate_definitions.items():
            passed, details = self._check_single_gate(gate_def, node_metrics, observations)
            
            # 保存结果
            gate_result = GateCheckResult(
                trace_id=trace_id,
                gate_definition_id=gate_def.id,
                passed=passed,
                check_details=details,
                checked_at=datetime.utcnow().isoformat()
            )
            self.db.add(gate_result)
            
            gate_results[gate_type] = {
                "passed": passed,
                "details": details
            }
        
        return gate_results
    
    def _check_single_gate(
        self, 
        gate_def: GateDefinition, 
        node_metrics: Dict,
        observations: List[Dict]
    ) -> tuple:
        """检查单个 Gate"""
        conditions = gate_def.pass_conditions
        details = {}
        all_passed = True
        
        for condition_key, threshold in conditions.items():
            # 检查各条件
            actual_value = self._get_gate_condition_value(condition_key, node_metrics, observations)
            
            if isinstance(threshold, bool):
                passed = actual_value == threshold
            elif isinstance(threshold, (int, float)):
                passed = actual_value is not None and actual_value >= threshold
            else:
                passed = actual_value is not None
            
            details[condition_key] = {
                "threshold": threshold,
                "actual": actual_value,
                "passed": passed
            }
            
            if not passed:
                all_passed = False
        
        return all_passed, details
    
    def _get_gate_condition_value(
        self, 
        condition_key: str, 
        node_metrics: Dict,
        observations: List[Dict]
    ) -> Any:
        """获取 Gate 条件的实际值"""
        # 根据条件名称获取值
        if "compile_success" in condition_key:
            compile_obs = [o for o in observations if "compile" in o.get("name", "").lower()]
            if compile_obs:
                success_count = sum(1 for o in compile_obs if o.get("level") != "ERROR")
                return success_count == len(compile_obs)
            return True
        
        if "recall_coverage" in condition_key:
            return node_metrics.get("search_strategy", {}).get("success_rate", 0.8)
        
        if "evidence_complete" in condition_key:
            return True  # 简化处理
        
        if "output_structure_valid" in condition_key:
            return True  # 简化处理
        
        if "plan_reasonable" in condition_key:
            return True  # 简化处理
        
        if "report_complete" in condition_key:
            report_obs = [o for o in observations if "report" in o.get("name", "").lower()]
            return len(report_obs) > 0
        
        if "hallucination_rate" in condition_key:
            return 0.05  # 简化处理
        
        if "query_answer_rate" in condition_key:
            return 0.85  # 简化处理
        
        return None
    
    async def _aggregate_layer_scores(
        self, 
        trace_id: uuid.UUID, 
        node_scores: Dict[str, Dict]
    ) -> Dict[str, float]:
        """层级聚合得分"""
        layer_scores = {}
        
        for layer_name in ["Layer0", "Layer1", "Layer2"]:
            # 筛选该层的节点
            layer_nodes = {
                code: scores for code, scores in node_scores.items()
                if self._get_layer_from_eval_layer(scores.get("eval_layer", "")) == layer_name
            }
            
            if not layer_nodes:
                layer_scores[layer_name] = 0.0
                continue
            
            # 计算加权平均
            total_weight = 0
            weighted_sum = 0
            
            for code, scores in layer_nodes.items():
                final_score = scores.get("final_score")
                if final_score is None:
                    continue
                
                # Gate 节点权重 ×1.5
                weight = 1.5 if scores.get("is_gate") else 1.0
                weighted_sum += final_score * weight
                total_weight += weight
            
            aggregate_score = weighted_sum / total_weight if total_weight > 0 else 0.0
            layer_scores[layer_name] = aggregate_score
            
            # 保存到数据库
            layer_result = LayerAggregateScore(
                trace_id=trace_id,
                layer=layer_name,
                node_scores={code: {"score": s.get("final_score"), "is_gate": s.get("is_gate")} 
                            for code, s in layer_nodes.items()},
                aggregate_score=aggregate_score,
                layer_weight=self.LAYER_WEIGHTS.get(layer_name, 0.0),
                weighted_score=aggregate_score * self.LAYER_WEIGHTS.get(layer_name, 0.0)
            )
            self.db.add(layer_result)
        
        return layer_scores
    
    def _get_layer_from_eval_layer(self, eval_layer: str) -> str:
        """从 eval_layer 字段提取层级"""
        if "L0" in eval_layer or "MainAgent" in eval_layer:
            return "Layer0"
        elif "L1" in eval_layer or "单体" in eval_layer:
            return "Layer1"
        elif "L2" in eval_layer or "协作" in eval_layer:
            return "Layer2"
        elif "L3" in eval_layer or "系统" in eval_layer:
            return "Layer2"  # L3 归入 Layer2 计算
        return "Layer1"  # 默认
    
    async def _calculate_investigation_score(
        self, 
        trace_id: uuid.UUID, 
        layer_scores: Dict[str, float],
        gate_results: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """计算 Investigation 总分"""
        # 总分 = Layer0*0.3 + Layer1*0.3 + Layer2*0.4
        total_score = (
            layer_scores.get("Layer0", 0) * 0.3 +
            layer_scores.get("Layer1", 0) * 0.3 +
            layer_scores.get("Layer2", 0) * 0.4
        )
        
        # Gate 通过情况
        gates_passed = {k: v["passed"] for k, v in gate_results.items()}
        all_gates_passed = all(gates_passed.values())
        
        # 质量等级
        quality_level = "F"
        for threshold, level in self.QUALITY_LEVELS:
            if total_score >= threshold:
                quality_level = level
                break
        
        # 是否需要人工复核
        needs_human_review = not all_gates_passed or total_score < 0.6
        
        # 保存到数据库
        investigation_score = InvestigationScore(
            trace_id=trace_id,
            layer0_score=layer_scores.get("Layer0", 0),
            layer1_score=layer_scores.get("Layer1", 0),
            layer2_score=layer_scores.get("Layer2", 0),
            total_score=total_score,
            gates_passed=gates_passed,
            all_gates_passed=all_gates_passed,
            quality_level=quality_level,
            needs_human_review=needs_human_review
        )
        self.db.add(investigation_score)
        
        return {
            "total_score": total_score,
            "quality_level": quality_level,
            "all_gates_passed": all_gates_passed,
            "needs_human_review": needs_human_review
        }
    
    async def close(self):
        """关闭资源"""
        await self.collector.close()
