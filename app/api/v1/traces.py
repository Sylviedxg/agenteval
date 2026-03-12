from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.trace import Trace
from app.schemas.trace import TraceCreate, TraceResponse

router = APIRouter(prefix="/traces", tags=["traces"])


@router.get("", response_model=List[TraceResponse])
async def get_traces(
    skip: int = 0,
    limit: int = 100,
    experiment_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Trace)
    if experiment_id:
        query = query.where(Trace.experiment_id == experiment_id)
    query = query.offset(skip).limit(limit).order_by(Trace.created_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=TraceResponse, status_code=status.HTTP_201_CREATED)
async def create_trace(
    data: TraceCreate,
    db: AsyncSession = Depends(get_db)
):
    trace = Trace(**data.model_dump())
    db.add(trace)
    await db.flush()
    await db.refresh(trace)
    return trace


@router.get("/{trace_id}", response_model=TraceResponse)
async def get_trace(
    trace_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Trace).where(Trace.id == trace_id)
    )
    trace = result.scalar_one_or_none()
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace not found"
        )
    return trace
