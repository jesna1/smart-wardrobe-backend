import asyncio
from app.db.session import AsyncSessionLocal
from app.models.wardrobe import Category
from sqlalchemy import select

CATEGORIES = [
    {"id": 1, "name": "Dresses"},
    {"id": 2, "name": "Tops"},
    {"id": 3, "name": "Bottoms"},
    {"id": 4, "name": "Outerwear"},
    {"id": 5, "name": "Shoes"},
]

async def seed():
    async with AsyncSessionLocal() as session:
        for cat_data in CATEGORIES:
            existing = await session.execute(
                select(Category).where(Category.id == cat_data["id"])
            )
            if not existing.scalars().first():
                session.add(Category(**cat_data))
        await session.commit()
        print("✅ Categories seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
