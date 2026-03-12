from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.experiment import EvalPlanCreate, EvalPlanResponse
from app.services import experiment_service

router = APIRouter(prefix="/eval-plans", tags=["eval-plans"])


@router.get("", response_model=List[EvalPlanResponse])
async def get_eval_plans(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    eval_plans = await experiment_service.get_eval_plans(db, skip=skip, limit=limit)
    return eval_plans


@router.post("", response_model=EvalPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_eval_plan(
    data: EvalPlanCreate,
    db: AsyncSession = Depends(get_db)
):
    eval_plan = await experiment_service.create_eval_plan(db, data)
    return eval_plan


@router.get("/{eval_plan_id}", response_model=EvalPlanResponse)
async def get_eval_plan(
    eval_plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    eval_plan = await experiment_service.get_eval_plan(db, eval_plan_id)
    if not eval_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eval plan not found"
        )
    return eval_plan
