from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import Experiment, EvalPlan, ConfigSnapshot
from app.models.dataset import Dataset
from app.schemas.experiment import (
    ExperimentCreate, ExperimentUpdate,
    DatasetCreate, EvalPlanCreate, ConfigSnapshotCreate
)


async def get_experiments(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[Experiment]:
    result = await db.execute(
        select(Experiment).offset(skip).limit(limit).order_by(Experiment.created_at.desc())
    )
    return list(result.scalars().all())


async def get_experiment(db: AsyncSession, experiment_id: UUID) -> Optional[Experiment]:
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    return result.scalar_one_or_none()


async def create_experiment(db: AsyncSession, data: ExperimentCreate) -> Experiment:
    experiment_data = data.model_dump()
    
    if experiment_data.get('config_snapshot_id') is None:
        snapshot = ConfigSnapshot(
            product_id=data.product_id,
            snapshot_name=f"Auto snapshot for experiment"
        )
        db.add(snapshot)
        await db.flush()
        experiment_data['config_snapshot_id'] = snapshot.id
    
    if experiment_data.get('eval_plan_id') is None:
        eval_plan = EvalPlan(
            name=f"Default eval plan"
        )
        db.add(eval_plan)
        await db.flush()
        experiment_data['eval_plan_id'] = eval_plan.id
    
    experiment = Experiment(**experiment_data)
    db.add(experiment)
    await db.flush()
    await db.refresh(experiment)
    return experiment


async def update_experiment_status(
    db: AsyncSession,
    experiment_id: UUID,
    status: str
) -> Optional[Experiment]:
    experiment = await get_experiment(db, experiment_id)
    if not experiment:
        return None
    
    experiment.status = status
    await db.flush()
    await db.refresh(experiment)
    return experiment


async def get_datasets(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[Dataset]:
    result = await db.execute(
        select(Dataset).offset(skip).limit(limit).order_by(Dataset.created_at.desc())
    )
    return list(result.scalars().all())


async def get_dataset(db: AsyncSession, dataset_id: UUID) -> Optional[Dataset]:
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id)
    )
    return result.scalar_one_or_none()


async def create_dataset(db: AsyncSession, data: DatasetCreate) -> Dataset:
    dataset = Dataset(**data.model_dump())
    db.add(dataset)
    await db.flush()
    await db.refresh(dataset)
    return dataset


async def get_eval_plans(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[EvalPlan]:
    result = await db.execute(
        select(EvalPlan).offset(skip).limit(limit).order_by(EvalPlan.created_at.desc())
    )
    return list(result.scalars().all())


async def get_eval_plan(db: AsyncSession, eval_plan_id: UUID) -> Optional[EvalPlan]:
    result = await db.execute(
        select(EvalPlan).where(EvalPlan.id == eval_plan_id)
    )
    return result.scalar_one_or_none()


async def create_eval_plan(db: AsyncSession, data: EvalPlanCreate) -> EvalPlan:
    eval_plan = EvalPlan(**data.model_dump())
    db.add(eval_plan)
    await db.flush()
    await db.refresh(eval_plan)
    return eval_plan
