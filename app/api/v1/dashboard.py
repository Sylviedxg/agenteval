from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.models.experiment import Experiment
from app.models.badcase import BadCase
from app.models.product import Product


class RecentExperiment(BaseModel):
    id: str
    name: str
    status: str
    overall_score: Optional[float] = None
    created_at: str


class DashboardStats(BaseModel):
    total_experiments: int
    total_badcases: int
    open_badcases: int
    resolved_badcases: int
    total_products: int
    recent_experiments: List[RecentExperiment]


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    total_experiments_result = await db.execute(select(func.count(Experiment.id)))
    total_experiments = total_experiments_result.scalar() or 0

    total_badcases_result = await db.execute(select(func.count(BadCase.id)))
    total_badcases = total_badcases_result.scalar() or 0

    open_badcases_result = await db.execute(
        select(func.count(BadCase.id)).where(BadCase.status == "open")
    )
    open_badcases = open_badcases_result.scalar() or 0

    resolved_badcases_result = await db.execute(
        select(func.count(BadCase.id)).where(BadCase.status == "resolved")
    )
    resolved_badcases = resolved_badcases_result.scalar() or 0

    total_products_result = await db.execute(select(func.count(Product.id)))
    total_products = total_products_result.scalar() or 0

    recent_experiments_result = await db.execute(
        select(Experiment).order_by(Experiment.created_at.desc()).limit(5)
    )
    recent_experiments = [
        RecentExperiment(
            id=str(exp.id),
            name=exp.name,
            status=exp.status,
            overall_score=exp.overall_score,
            created_at=exp.created_at.isoformat()
        )
        for exp in recent_experiments_result.scalars().all()
    ]

    return DashboardStats(
        total_experiments=total_experiments,
        total_badcases=total_badcases,
        open_badcases=open_badcases,
        resolved_badcases=resolved_badcases,
        total_products=total_products,
        recent_experiments=recent_experiments
    )
