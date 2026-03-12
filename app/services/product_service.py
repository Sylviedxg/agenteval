from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


async def get_products(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[Product]:
    result = await db.execute(
        select(Product).offset(skip).limit(limit).order_by(Product.created_at.desc())
    )
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: UUID) -> Optional[Product]:
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession,
    product_id: UUID,
    data: ProductUpdate
) -> Optional[Product]:
    product = await get_product(db, product_id)
    if not product:
        return None
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await db.flush()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product_id: UUID) -> bool:
    product = await get_product(db, product_id)
    if not product:
        return False
    
    await db.delete(product)
    await db.flush()
    return True
