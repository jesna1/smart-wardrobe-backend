import itertools
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.wardrobe import WardrobeItem
from app.schemas.stylist import (
    StylistRecommendationResponse,
    OutfitRecommendation,
    RecommendedItem,
    WeatherInfo,
)

router = APIRouter()

@router.get("/recommendations", response_model=StylistRecommendationResponse)
async def get_stylist_recommendations(
    occasion: str = Query("Work", description="Target occasion (e.g. Work, Casual, Formal, Evening, Gym)"),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Contextual weather info (e.g. Doha context)
        weather_data = WeatherInfo(
            temperature_c=32.0,
            condition="Sunny & Clear",
            location="Doha, Qatar",
            humidity=50,
            icon_code="01d"
        )

        # 2. Fetch wardrobe items asynchronously from database
        result = await db.execute(select(WardrobeItem))
        db_items = result.scalars().all()

        # Transform DB items into schema items
        user_items: List[RecommendedItem] = []
        for item in db_items:
            user_items.append(
                RecommendedItem(
                    id=int(item.id) if str(item.id).isdigit() else hash(item.id) % 10000,
                    title=getattr(item, "title", "Wardrobe Item"),
                    category=getattr(item, "category", "top").lower(),
                    image_url=getattr(item, "image_url", None),
                    color=getattr(item, "color", "Neutral"),
                )
            )

        # Fallback inventory seed if database has fewer than 3 items
        if len(user_items) < 3:
            user_items = [
                RecommendedItem(
                    id=101,
                    title="Tailored Navy Blazer",
                    category="top",
                    image_url="https://images.unsplash.com/photo-1594938298603-c8148c4dae35",
                    color="Navy"
                ),
                RecommendedItem(
                    id=102,
                    title="White Linen Shirt",
                    category="top",
                    image_url="https://images.unsplash.com/photo-1598033129183-c4f50c736f10",
                    color="White"
                ),
                RecommendedItem(
                    id=103,
                    title="Slim-fit Chino Trousers",
                    category="bottom",
                    image_url="https://images.unsplash.com/photo-1473966968600-fa801b869a1a",
                    color="Beige"
                ),
                RecommendedItem(
                    id=104,
                    title="Classic Leather Loafers",
                    category="footwear",
                    image_url="https://images.unsplash.com/photo-1533867617858-e7b97e060509",
                    color="Brown"
                ),
            ]

        # 3. Group items into outfit slots
        tops = [i for i in user_items if i.category in ["top", "shirt", "blouse", "jacket", "blazer"]]
        bottoms = [i for i in user_items if i.category in ["bottom", "pants", "trousers", "skirt", "shorts"]]
        shoes = [i for i in user_items if i.category in ["footwear", "shoes", "sneakers", "loafers"]]

        # Ensure fallback lists have at least one item per category
        if not tops:
            tops = user_items[:1]
        if not bottoms:
            bottoms = user_items[1:2] if len(user_items) > 1 else user_items[:1]
        if not shoes:
            shoes = user_items[2:3] if len(user_items) > 2 else user_items[:1]

        # 4. Generate dynamic outfit combinations
        recommendations: List[OutfitRecommendation] = []
        outfit_counter = 1

        for top, bottom, shoe in itertools.product(tops, bottoms, shoes):
            if outfit_counter > 3:
                break

            # Calculate dynamic score & rationale based on weather & occasion
            match_score = 92 if occasion.lower() in ["work", "formal"] else 88
            rationale = (
                f"Lightweight {top.color} {top.title.lower()} paired with {bottom.title.lower()} "
                f"provides breathability in {weather_data.temperature_c:.0f}°C weather while maintaining a polished {occasion.lower()} look."
            )

            recommendations.append(
                OutfitRecommendation(
                    outfit_id=1000 + outfit_counter,
                    title=f"Curated {occasion} Ensemble #{outfit_counter}",
                    occasion=occasion,
                    match_score=match_score - (outfit_counter * 2),
                    ai_rationale=rationale,
                    is_saved=False,
                    items=[top, bottom, shoe],
                )
            )
            outfit_counter += 1

        return {
            "status": "success",
            "occasion": occasion,
            "weather": weather_data,
            "recommendations": recommendations,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate stylist recommendations: {str(e)}"
        )