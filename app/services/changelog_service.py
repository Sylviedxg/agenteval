from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badcase import Changelog
from app.schemas.changelog import ChangelogCreate


async def get_changelogs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[UUID] = None,
    change_type: Optional[str] = None
) -> List[Changelog]:
    query = select(Changelog)
    
    if product_id:
        query = query.where(Changelog.product_id == product_id)
    if change_type:
        query = query.where(Changelog.change_type == change_type)
    
    query = query.offset(skip).limit(limit).order_by(Changelog.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_changelog(db: AsyncSession, changelog_id: UUID) -> Optional[Changelog]:
    result = await db.execute(
        select(Changelog).where(Changelog.id == changelog_id)
    )
    return result.scalar_one_or_none()


async def create_changelog(db: AsyncSession, data: ChangelogCreate) -> Changelog:
    changelog = Changelog(**data.model_dump())
    db.add(changelog)
    await db.flush()
    await db.refresh(changelog)
    return changelog
