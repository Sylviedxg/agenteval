from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badcase import BadCase
from app.schemas.badcase import BadCaseCreate, BadCaseUpdate


async def get_badcases(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    experiment_id: Optional[UUID] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None
) -> List[BadCase]:
    query = select(BadCase)
    
    if experiment_id:
        query = query.where(BadCase.experiment_id == experiment_id)
    if severity:
        query = query.where(BadCase.severity == severity)
    if status:
        query = query.where(BadCase.status == status)
    
    query = query.offset(skip).limit(limit).order_by(BadCase.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_badcase(db: AsyncSession, badcase_id: UUID) -> Optional[BadCase]:
    result = await db.execute(
        select(BadCase).where(BadCase.id == badcase_id)
    )
    return result.scalar_one_or_none()


async def create_badcase(db: AsyncSession, data: BadCaseCreate) -> BadCase:
    badcase = BadCase(**data.model_dump())
    db.add(badcase)
    await db.flush()
    await db.refresh(badcase)
    return badcase


async def update_badcase(
    db: AsyncSession,
    badcase_id: UUID,
    data: BadCaseUpdate
) -> Optional[BadCase]:
    badcase = await get_badcase(db, badcase_id)
    if not badcase:
        return None
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(badcase, field, value)
    
    await db.flush()
    await db.refresh(badcase)
    return badcase


async def delete_badcase(db: AsyncSession, badcase_id: UUID) -> bool:
    badcase = await get_badcase(db, badcase_id)
    if not badcase:
        return False
    
    await db.delete(badcase)
    await db.flush()
    return True
