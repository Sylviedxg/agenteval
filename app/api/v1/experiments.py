from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.experiment import ExperimentCreate, ExperimentResponse
from app.services import experiment_service

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=List[ExperimentResponse])
async def get_experiments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    experiments = await experiment_service.get_experiments(db, skip=skip, limit=limit)
    return experiments


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    data: ExperimentCreate,
    db: AsyncSession = Depends(get_db)
):
    experiment = await experiment_service.create_experiment(db, data)
    return experiment


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    experiment = await experiment_service.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found"
        )
    return experiment


@router.patch("/{experiment_id}/status", response_model=ExperimentResponse)
async def update_experiment_status(
    experiment_id: UUID,
    status_value: str,
    db: AsyncSession = Depends(get_db)
):
    experiment = await experiment_service.update_experiment_status(db, experiment_id, status_value)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found"
        )
    return experiment
