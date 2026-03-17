"""
Langfuse 数据采集服务
从 Langfuse API 获取 trace 数据，提取客观指标
"""
import httpx
from typing import Optional, Dict, List, Any
from datetime import datetime
import base64


class LangfuseCollector:
    """Langfuse 数据采集器"""
    
    def __init__(
        self,
        host: str = "http://172.21.30.114:3208",
        public_key: str = "",
        secret_key: str = ""
    ):
        self.host = host.rstrip("/")
        self.public_key = public_key
        self.secret_key = secret_key
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def auth_header(self) -> str:
        """生成 Basic Auth header"""
        credentials = f"{self.public_key}:{self.secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.host,
                headers={"Authorization": self.auth_header},
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get_trace(self, trace_id: str) -> Optional[Dict]:
        """获取单个 trace 详情（从 traces 列表中筛选）"""
        client = await self._get_client()
        try:
            # 直接获取 trace 可能因为太大而失败，改用列表接口
            resp = await client.get(f"/api/public/traces/{trace_id}")
            if resp.status_code == 200:
                return resp.json()
            # 如果失败，尝试从列表中获取
            resp = await client.get("/api/public/traces", params={"limit": 100})
            if resp.status_code == 200:
                data = resp.json()
                for trace in data.get("data", []):
                    if trace.get("id") == trace_id:
                        return trace
            return None
        except Exception as e:
            print(f"Error fetching trace {trace_id}: {e}")
            return None
    
    async def get_trace_observations(self, trace_id: str, max_count: int = 0) -> List[Dict]:
        """获取 trace 的所有 observations (spans/generations)，分页获取
        max_count: 最大获取数量，0表示不限制
        """
        client = await self._get_client()
        all_observations = []
        page = 1
        
        try:
            while True:
                resp = await client.get(
                    "/api/public/observations",
                    params={"traceId": trace_id, "limit": 100, "page": page}
                )
                if resp.status_code != 200:
                    print(f"Error fetching observations page {page}: {resp.status_code}")
                    break
                
                data = resp.json()
                observations = data.get("data", [])
                if not observations:
                    break
                
                all_observations.extend(observations)
                
                # 检查是否达到max_count限制
                if max_count > 0 and len(all_observations) >= max_count:
                    all_observations = all_observations[:max_count]
                    break
                
                # 检查是否还有更多页
                meta = data.get("meta", {})
                total_items = meta.get("totalItems", len(all_observations))
                if len(all_observations) >= total_items:
                    break
                
                page += 1
                # 安全限制，最多获取50页
                if page > 50:
                    break
            
            return all_observations
        except Exception as e:
            print(f"Error fetching observations for trace {trace_id}: {e}")
            return all_observations
    
    async def list_traces(
        self,
        project_id: str = "cmkwt46of0004nz092h2z9alq",
        limit: int = 50,
        name: Optional[str] = None
    ) -> List[Dict]:
        """列出 traces"""
        client = await self._get_client()
        try:
            params = {"limit": limit}
            if name:
                params["name"] = name
            resp = await client.get("/api/public/traces", params=params)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", [])
            return []
        except Exception as e:
            print(f"Error listing traces: {e}")
            return []
    
    def extract_node_metrics(self, observations: List[Dict]) -> Dict[str, Dict]:
        """
        从 observations 中提取各节点的客观指标
        返回: {node_code: {metric_name: value, raw_obs: [...]}}
        """
        node_metrics = {}
        
        # 按 name 分组 observations
        obs_by_name = {}
        obs_by_type = {"SPAN": [], "GENERATION": [], "EVENT": []}
        for obs in observations:
            name = obs.get("name", "unknown")
            obs_type = obs.get("type", "SPAN")
            if name not in obs_by_name:
                obs_by_name[name] = []
            obs_by_name[name].append(obs)
            if obs_type in obs_by_type:
                obs_by_type[obs_type].append(obs)
        
        # 提取 MainAgent 相关指标
        if "MainAgent" in obs_by_name:
            main_obs = obs_by_name["MainAgent"][0]
            node_metrics["main_llm_call"] = {
                "success": main_obs.get("status") == "success" or main_obs.get("level") != "ERROR",
                "latency_ms": self._calc_duration_ms(main_obs),
                "total_tokens": self._sum_tokens(obs_by_name.get("ChatOpenAI", []))
            }
        
        # 提取 plan_parallel 指标
        if "plan_parallel" in obs_by_name:
            plan_obs = obs_by_name["plan_parallel"][0]
            node_metrics["main_plan_parallel"] = {
                "latency_ms": self._calc_duration_ms(plan_obs),
                "success": plan_obs.get("level") != "ERROR"
            }
        
        # 提取 delegate 指标
        if "delegate" in obs_by_name:
            delegate_obs = obs_by_name["delegate"]
            success_count = sum(1 for o in delegate_obs if o.get("level") != "ERROR")
            node_metrics["main_delegate"] = {
                "success_rate": success_count / len(delegate_obs) if delegate_obs else 0,
                "total_delegates": len(delegate_obs)
            }
        
        # 提取 CardAgent 通用指标
        for card_type in ["SearchCardAgent", "ChartCardAgent", "MapCardAgent", 
                          "NetworkCardAgent", "TimelineCardAgent", "ReportCardAgentV2"]:
            if card_type in obs_by_name:
                card_obs = obs_by_name[card_type][0]
                node_code = self._card_type_to_node_code(card_type)
                node_metrics[node_code] = {
                    "latency_ms": self._calc_duration_ms(card_obs),
                    "success": card_obs.get("level") != "ERROR"
                }
        
        # 提取 LLM 调用指标 (ChatOpenAI)
        if "ChatOpenAI" in obs_by_name:
            llm_obs = obs_by_name["ChatOpenAI"]
            total_tokens = self._sum_tokens(llm_obs)
            total_cost = sum(o.get("calculatedTotalCost", 0) or 0 for o in llm_obs)
            avg_latency = sum(self._calc_duration_ms(o) for o in llm_obs) / len(llm_obs) if llm_obs else 0
            
            node_metrics["card_llm_inference"] = {
                "total_calls": len(llm_obs),
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "avg_latency_ms": avg_latency,
                "success_rate": sum(1 for o in llm_obs if o.get("level") != "ERROR") / len(llm_obs) if llm_obs else 0
            }
        
        # 提取工具调用指标
        tool_calls = [o for o in observations if o.get("type") == "SPAN" and 
                      any(t in o.get("name", "") for t in ["web_search", "browse_url", "e2b_"])]
        if tool_calls:
            success_count = sum(1 for o in tool_calls if o.get("level") != "ERROR")
            node_metrics["card_tool_calls"] = {
                "total_calls": len(tool_calls),
                "success_rate": success_count / len(tool_calls) if tool_calls else 0,
                "avg_latency_ms": sum(self._calc_duration_ms(o) for o in tool_calls) / len(tool_calls) if tool_calls else 0
            }
        
        # 提取 compile_gate 指标
        compile_gates = [o for o in observations if "compile" in o.get("name", "").lower() and "gate" in o.get("name", "").lower()]
        if compile_gates:
            success_count = sum(1 for o in compile_gates if o.get("level") != "ERROR")
            node_metrics["chart_compile_gate"] = {
                "success_rate": success_count / len(compile_gates) if compile_gates else 0,
                "total_rounds": len(compile_gates),
                "avg_latency_ms": sum(self._calc_duration_ms(o) for o in compile_gates) / len(compile_gates) if compile_gates else 0
            }
        
        # 提取 chapter_writer 指标
        chapter_writers = [o for o in observations if "chapter_writer" in o.get("name", "").lower()]
        if chapter_writers:
            node_metrics["report_chapter_write"] = {
                "total_chapters": len(chapter_writers),
                "avg_latency_ms": sum(self._calc_duration_ms(o) for o in chapter_writers) / len(chapter_writers) if chapter_writers else 0,
                "success_rate": sum(1 for o in chapter_writers if o.get("level") != "ERROR") / len(chapter_writers) if chapter_writers else 0
            }
        
        # 提取 bubble_finding 指标
        bubbles = [o for o in observations if "bubble" in o.get("name", "").lower()]
        if bubbles:
            node_metrics["card_bubble"] = {
                "total_bubbles": len(bubbles),
                "success_rate": 1.0  # bubbles 通常都成功
            }
        
        return node_metrics
    
    def _calc_duration_ms(self, obs: Dict) -> float:
        """计算 observation 的持续时间（毫秒）"""
        start = obs.get("startTime")
        end = obs.get("endTime")
        if start and end:
            try:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                return (end_dt - start_dt).total_seconds() * 1000
            except:
                pass
        return obs.get("latency", 0) * 1000 if obs.get("latency") else 0
    
    def _sum_tokens(self, observations: List[Dict]) -> int:
        """计算 token 总数"""
        total = 0
        for obs in observations:
            usage = obs.get("usage", {}) or {}
            total += usage.get("totalTokens", 0) or 0
            total += usage.get("total", 0) or 0
        return total
    
    def _card_type_to_node_code(self, card_type: str) -> str:
        """将 CardAgent 类型转换为节点编码"""
        mapping = {
            "SearchCardAgent": "search_strategy",
            "ChartCardAgent": "chart_data_fetch",
            "MapCardAgent": "map_code_gen",
            "NetworkCardAgent": "network_code_gen",
            "TimelineCardAgent": "timeline_code_gen",
            "ReportCardAgentV2": "report_collect_context"
        }
        return mapping.get(card_type, card_type.lower())
    
    async def collect_trace_metrics(self, trace_id: str) -> Dict[str, Any]:
        """
        采集单个 trace 的完整指标数据
        返回: {
            "trace_info": {...},
            "node_metrics": {node_code: {...}},
            "summary": {...}
        }
        """
        trace = await self.get_trace(trace_id)
        if not trace:
            return {"error": f"Trace {trace_id} not found"}
        
        observations = await self.get_trace_observations(trace_id)
        node_metrics = self.extract_node_metrics(observations)
        
        # 计算汇总指标
        total_latency = trace.get("latency", 0) or 0
        total_cost = trace.get("totalCost", 0) or 0
        total_tokens = sum(
            (obs.get("usage", {}) or {}).get("totalTokens", 0) or 0
            for obs in observations
        )
        
        error_count = sum(1 for obs in observations if obs.get("level") == "ERROR")
        
        return {
            "trace_info": {
                "id": trace.get("id"),
                "name": trace.get("name"),
                "session_id": trace.get("sessionId"),
                "user_id": trace.get("userId"),
                "metadata": trace.get("metadata", {}),
                "timestamp": trace.get("timestamp"),
                "latency_ms": total_latency * 1000 if total_latency < 1000 else total_latency,
                "total_cost": total_cost,
                "total_tokens": total_tokens
            },
            "node_metrics": node_metrics,
            "observations_count": len(observations),
            "error_count": error_count,
            "summary": {
                "total_latency_ms": total_latency * 1000 if total_latency < 1000 else total_latency,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "error_rate": error_count / len(observations) if observations else 0,
                "nodes_extracted": len(node_metrics)
            }
        }
