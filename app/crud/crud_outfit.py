from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.wardrobe import Outfit, WardrobeItem
from app.schemas.outfit import OutfitCreate
from typing import List

async def create_outfit(db: AsyncSession, outfit_in: OutfitCreate, user_id: int) -> Outfit:
    result = await db.execute(
        select(WardrobeItem).where(
            WardrobeItem.id.in_(outfit_in.item_ids),
            WardrobeItem.user_id == user_id
        )
    )
    items = list(result.scalars().all())

    db_outfit = Outfit(
        name=outfit_in.name,
        description=outfit_in.description,
        occasion=outfit_in.occasion,
        user_id=user_id,
        items=items
    )
    db.add(db_outfit)
    await db.commit()

    res = await db.execute(
        select(Outfit)
        .options(selectinload(Outfit.items))
        .where(Outfit.id == db_outfit.id)
    )
    return res.scalars().first()

async def get_user_outfits(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Outfit]:
    result = await db.execute(
        select(Outfit)
        .options(selectinload(Outfit.items))
        .where(Outfit.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
