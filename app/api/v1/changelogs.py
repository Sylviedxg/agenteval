from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.changelog import ChangelogCreate, ChangelogResponse
from app.services import changelog_service

router = APIRouter(prefix="/changelogs", tags=["changelogs"])


@router.get("", response_model=List[ChangelogResponse])
async def get_changelogs(
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[UUID] = Query(None),
    change_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    changelogs = await changelog_service.get_changelogs(
        db, skip=skip, limit=limit,
        product_id=product_id,
        change_type=change_type
    )
    return changelogs


@router.post("", response_model=ChangelogResponse, status_code=status.HTTP_201_CREATED)
async def create_changelog(
    data: ChangelogCreate,
    db: AsyncSession = Depends(get_db)
):
    changelog = await changelog_service.create_changelog(db, data)
    return changelog


@router.get("/{changelog_id}", response_model=ChangelogResponse)
async def get_changelog(
    changelog_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    changelog = await changelog_service.get_changelog(db, changelog_id)
    if not changelog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Changelog not found"
        )
    return changelog
