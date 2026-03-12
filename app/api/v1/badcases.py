from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.badcase import BadCaseCreate, BadCaseUpdate, BadCaseResponse
from app.services import badcase_service

router = APIRouter(prefix="/badcases", tags=["badcases"])


@router.get("", response_model=List[BadCaseResponse])
async def get_badcases(
    skip: int = 0,
    limit: int = 100,
    experiment_id: Optional[UUID] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    badcases = await badcase_service.get_badcases(
        db, skip=skip, limit=limit,
        experiment_id=experiment_id,
        severity=severity,
        status=status
    )
    return badcases


@router.post("", response_model=BadCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_badcase(
    data: BadCaseCreate,
    db: AsyncSession = Depends(get_db)
):
    badcase = await badcase_service.create_badcase(db, data)
    return badcase


@router.get("/{badcase_id}", response_model=BadCaseResponse)
async def get_badcase(
    badcase_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    badcase = await badcase_service.get_badcase(db, badcase_id)
    if not badcase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BadCase not found"
        )
    return badcase


@router.patch("/{badcase_id}", response_model=BadCaseResponse)
async def update_badcase(
    badcase_id: UUID,
    data: BadCaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    badcase = await badcase_service.update_badcase(db, badcase_id, data)
    if not badcase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BadCase not found"
        )
    return badcase


@router.delete("/{badcase_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_badcase(
    badcase_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    success = await badcase_service.delete_badcase(db, badcase_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BadCase not found"
        )
