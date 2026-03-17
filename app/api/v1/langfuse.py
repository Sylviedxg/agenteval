"""
Langfuse 数据采集 API
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.langfuse_collector import LangfuseCollector

router = APIRouter(prefix="/langfuse", tags=["Langfuse数据采集"])

# 默认配置 - 实际使用时应从环境变量读取
DEFAULT_HOST = "http://172.21.30.114:3208"
DEFAULT_PUBLIC_KEY = "pk-lf-63c63e3a-c38a-45f7-b173-13586793e22e"
DEFAULT_SECRET_KEY = ""  # 需要配置


class LangfuseConfig(BaseModel):
    host: str = DEFAULT_HOST
    public_key: str = DEFAULT_PUBLIC_KEY
    secret_key: str = ""


@router.post("/collect-trace/{trace_id}")
async def collect_trace_metrics(
    trace_id: str,
    config: Optional[LangfuseConfig] = None
):
    """
    从 Langfuse 采集单个 trace 的指标数据
    
    - trace_id: Langfuse trace ID
    - config: Langfuse 连接配置（可选）
    """
    if config is None:
        config = LangfuseConfig()
    
    if not config.secret_key:
        raise HTTPException(
            status_code=400, 
            detail="需要提供 Langfuse secret_key"
        )
    
    collector = LangfuseCollector(
        host=config.host,
        public_key=config.public_key,
        secret_key=config.secret_key
    )
    
    try:
        result = await collector.collect_trace_metrics(trace_id)
        return result
    finally:
        await collector.close()


@router.post("/list-traces")
async def list_traces(
    config: LangfuseConfig,
    limit: int = 50,
    name: Optional[str] = None
):
    """
    列出 Langfuse 中的 traces
    """
    if not config.secret_key:
        raise HTTPException(
            status_code=400,
            detail="需要提供 Langfuse secret_key"
        )
    
    collector = LangfuseCollector(
        host=config.host,
        public_key=config.public_key,
        secret_key=config.secret_key
    )
    
    try:
        traces = await collector.list_traces(limit=limit, name=name)
        return {
            "count": len(traces),
            "traces": [
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "timestamp": t.get("timestamp"),
                    "latency": t.get("latency"),
                    "totalCost": t.get("totalCost"),
                    "metadata": t.get("metadata", {})
                }
                for t in traces
            ]
        }
    finally:
        await collector.close()


@router.get("/test-connection")
async def test_langfuse_connection(
    host: str = DEFAULT_HOST,
    public_key: str = DEFAULT_PUBLIC_KEY,
    secret_key: str = ""
):
    """
    测试 Langfuse 连接
    """
    if not secret_key:
        return {"status": "error", "message": "需要提供 secret_key"}
    
    collector = LangfuseCollector(
        host=host,
        public_key=public_key,
        secret_key=secret_key
    )
    
    try:
        traces = await collector.list_traces(limit=1)
        return {
            "status": "connected",
            "host": host,
            "traces_available": len(traces) > 0
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        await collector.close()
