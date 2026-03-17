"""
评测集导入API
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.dataset import Dataset, Case
from app.services.dataset_importer import dataset_importer

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/import-excel")
async def import_dataset_from_excel(
    file: UploadFile = File(...),
    dataset_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    从Excel文件导入评测集
    
    - 解析tanqi_eval_v3.xlsx格式的评测集
    - 创建Dataset和Cases记录
    - 返回导入结果摘要
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传Excel文件(.xlsx或.xls)")
    
    content = await file.read()
    
    try:
        result = await dataset_importer.import_from_excel(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析Excel失败: {str(e)}")
    
    # 创建Dataset记录
    ds_name = dataset_name or file.filename.replace(".xlsx", "").replace(".xls", "")
    dataset = Dataset(
        id=uuid.uuid4(),
        name=ds_name,
        description=f"从{file.filename}导入",
        version="1.0.0",
        source_type="excel_import",
        metadata_={
            "nodes": result["nodes"],
            "scenarios": result["scenarios"],
            "summary": result["summary"]
        }
    )
    db.add(dataset)
    
    # 创建Case记录
    cases_created = []
    for case_data in result["cases"]:
        case = Case(
            id=uuid.UUID(case_data["id"]),
            dataset_id=dataset.id,
            name=case_data["case_name"],
            input_data={
                "query": case_data["input_query"],
                "scenario": case_data["scenario_name"],
                "capability": case_data["capability_name"]
            },
            expected_output=case_data["expected_output"],
            metadata_={
                "scenario_id": case_data["scenario_id"],
                "scenario_code": case_data["scenario_code"],
                "capability_code": case_data["capability_code"],
                "expected_scores": case_data["expected_scores"]
            },
            tags=[case_data["scenario_code"], case_data["capability_code"]]
        )
        db.add(case)
        cases_created.append({
            "id": str(case.id),
            "name": case.name,
            "scenario": case_data["scenario_name"],
            "capability": case_data["capability_name"]
        })
    
    await db.commit()
    await db.refresh(dataset)
    
    return {
        "success": True,
        "dataset": {
            "id": str(dataset.id),
            "name": dataset.name,
            "version": dataset.version
        },
        "summary": result["summary"],
        "cases": cases_created[:10],  # 只返回前10个预览
        "total_cases": len(cases_created)
    }


@router.get("/import-preview")
async def preview_import_excel(
    file: UploadFile = File(...)
):
    """
    预览Excel导入结果（不保存到数据库）
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传Excel文件(.xlsx或.xls)")
    
    content = await file.read()
    
    try:
        result = await dataset_importer.import_from_excel(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析Excel失败: {str(e)}")
    
    return {
        "success": True,
        "preview": True,
        "nodes": result["nodes"],
        "scenarios": result["scenarios"],
        "cases": result["cases"][:5],  # 只返回前5个预览
        "summary": result["summary"]
    }


@router.get("/{dataset_id}/nodes")
async def get_dataset_nodes(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取评测集的节点定义"""
    result = await db.execute(
        select(Dataset).where(Dataset.id == uuid.UUID(dataset_id))
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="评测集不存在")
    
    metadata = dataset.metadata_ or {}
    return {
        "dataset_id": str(dataset.id),
        "dataset_name": dataset.name,
        "nodes": metadata.get("nodes", []),
        "scenarios": metadata.get("scenarios", [])
    }


@router.get("/{dataset_id}/cases")
async def get_dataset_cases(
    dataset_id: str,
    scenario_code: Optional[str] = None,
    capability_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取评测集的测试用例"""
    query = select(Case).where(Case.dataset_id == uuid.UUID(dataset_id))
    
    result = await db.execute(query)
    cases = result.scalars().all()
    
    # 过滤
    filtered_cases = []
    for case in cases:
        metadata = case.metadata_ or {}
        if scenario_code and metadata.get("scenario_code") != scenario_code:
            continue
        if capability_code and metadata.get("capability_code") != capability_code:
            continue
        
        filtered_cases.append({
            "id": str(case.id),
            "name": case.name,
            "input_data": case.input_data,
            "expected_output": case.expected_output,
            "scenario_code": metadata.get("scenario_code"),
            "capability_code": metadata.get("capability_code"),
            "expected_scores": metadata.get("expected_scores", {}),
            "tags": case.tags
        })
    
    return {
        "dataset_id": dataset_id,
        "total": len(filtered_cases),
        "cases": filtered_cases
    }
