from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.wardrobe import Category, WardrobeItem

router = APIRouter()

@router.post("/seed", status_code=201)
async def seed_initial_data(db: AsyncSession = Depends(get_db)):
    categories = ["Tops", "Bottoms", "Outerwear", "Footwear", "Accessories"]
    for cat_name in categories:
        res = await db.execute(select(Category).where(Category.name == cat_name))
        if not res.scalars().first():
            db.add(Category(name=cat_name))
    await db.commit()

    # Add sample item with mock 512-dimension vector
    res = await db.execute(select(WardrobeItem).where(WardrobeItem.title == "Classic Navy Blazer"))
    if not res.scalars().first():
        mock_vector = [0.1] * 512
        item = WardrobeItem(
            title="Classic Navy Blazer",
            color="Navy",
            season="All-Season",
            category_id=3,
            embedding=mock_vector
        )
        db.add(item)
        await db.commit()

    return {"message": "Database seeded successfully with default categories and sample vector item."}
