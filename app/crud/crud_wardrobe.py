from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, defer

from app.models.wardrobe import WardrobeItem
from app.schemas.wardrobe import WardrobeItemCreate, WardrobeItemUpdate


async def create_wardrobe_item(db: AsyncSession, item_in: WardrobeItemCreate, user_id: int) -> WardrobeItem:
    item_data = item_in.model_dump()
    db_item = WardrobeItem(**item_data, user_id=user_id)
    db.add(db_item)
    await db.commit()
    
    # Directly refresh foreign key relationships post-commit
    if db_item.category_id:
        await db.refresh(db_item, ["category"])
        
    return db_item


async def get_wardrobe_items(
    db: AsyncSession, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    category_id: Optional[int] = None,
    season: Optional[str] = None,
    occasion: Optional[str] = None
) -> List[WardrobeItem]:
    query = (
        select(WardrobeItem)
        .options(
            selectinload(WardrobeItem.category),
            defer(WardrobeItem.embedding)
        )
        .where(WardrobeItem.user_id == user_id)
    )

    if category_id is not None:
        query = query.where(WardrobeItem.category_id == category_id)
    if season is not None:
        query = query.where(func.lower(WardrobeItem.season) == season.lower())
    if occasion is not None:
        # Case-insensitive occasion filter
        query = query.where(func.lower(WardrobeItem.occasion) == occasion.lower())

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_wardrobe_item_by_id(db: AsyncSession, item_id: int, user_id: int) -> Optional[WardrobeItem]:
    result = await db.execute(
        select(WardrobeItem)
        .options(
            selectinload(WardrobeItem.category),
            defer(WardrobeItem.embedding)
        )
        .where(WardrobeItem.id == item_id, WardrobeItem.user_id == user_id)
    )
    return result.scalars().first()


async def update_wardrobe_item(db: AsyncSession, item: WardrobeItem, item_update: WardrobeItemUpdate) -> WardrobeItem:
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.add(item)
    await db.commit()
    # Refetch with loaded category to avoid Async SQLAlchemy detached instance errors
    return await get_wardrobe_item_by_id(db=db, item_id=item.id, user_id=item.user_id)


async def delete_wardrobe_item(db: AsyncSession, item_id: int, user_id: int) -> bool:
    item = await get_wardrobe_item_by_id(db, item_id, user_id)
    if item:
        await db.delete(item)
        await db.commit()
        return True
    return False


async def search_similar_items(db: AsyncSession, user_id: int, vector: List[float], limit: int = 5) -> List[WardrobeItem]:
    result = await db.execute(
        select(WardrobeItem)
        .options(
            selectinload(WardrobeItem.category),
            defer(WardrobeItem.embedding)
        )
        .where(WardrobeItem.user_id == user_id)
        .order_by(WardrobeItem.embedding.l2_distance(vector))
        .limit(limit)
    )
    return list(result.scalars().all())