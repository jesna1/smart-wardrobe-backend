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
    occasion: str = Query("Work", description="Target occasion"),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Weather Context
        weather_data = WeatherInfo(
            temperature_c=38.4,
            temperature_f=101.1,
            condition="Sunny",
            humidity=33,
            wind_kph=15.1,
            season_category="Summer",
            location="Al Bida` Al Gharbiyah",
            icon_code="01d",
            is_fallback=False
        )

        # 2. Fetch wardrobe items asynchronously
        result = await db.execute(select(WardrobeItem))
        db_items = result.scalars().all()

        user_items: List[RecommendedItem] = []
        for item in db_items:
            user_items.append(
                RecommendedItem(
                    id=int(item.id) if str(item.id).isdigit() else hash(item.id) % 10000,
                    title=getattr(item, "title", "Wardrobe Item"),
                    category=str(getattr(item, "category", "top")).lower(),
                    image_url=getattr(item, "image_url", None),
                    color=getattr(item, "color", "Multi"),
                )
            )

        # Fallback inventory if wardrobe is empty or small
        if len(user_items) < 2:
            user_items = [
                RecommendedItem(
                    id=101,
                    title="Tailored Shirt",
                    category="top",
                    image_url="https://res.cloudinary.com/nyz80cs8/image/upload/v1788695922/smart_wardrobe/items/rhzj9o5zbbwo53yuyo9n.png",
                    color="Multi"
                ),
                RecommendedItem(
                    id=102,
                    title="Formal Trousers",
                    category="bottom",
                    image_url="https://res.cloudinary.com/nyz80cs8/image/upload/v1788696031/smart_wardrobe/items/c9knhwnqvtwxtpruaecm.png",
                    color="Multi"
                ),
            ]

        # 3. Separate by category
        tops = [i for i in user_items if i.category in ["top", "shirt", "blouse", "jacket", "blazer"]] or user_items[:1]
        bottoms = [i for i in user_items if i.category in ["bottom", "pants", "trousers", "skirt", "pant"]] or user_items[1:2]
        shoes = [i for i in user_items if i.category in ["shoes", "footwear", "sneakers", "loafers"]]

        # 4. Assemble outfit recommendations
        recommendations: List[OutfitRecommendation] = []
        counter = 1

        for top in tops:
            for bottom in bottoms:
                if counter > 3:
                    break
                
                combo = [top, bottom]
                if shoes:
                    combo.append(shoes[0])

                recommendations.append(
                    OutfitRecommendation(
                        outfit_id=counter,
                        title=f"Curated {occasion.capitalize()} Look #{counter}",
                        occasion=occasion.capitalize(),
                        match_score=92,
                        ai_rationale=f"Harmonious combination featuring {top.title} selected for {weather_data.temperature_c}°C weather.",
                        is_saved=False,
                        items=combo
                    )
                )
                counter += 1

        return StylistRecommendationResponse(
            weather=weather_data,
            occasion=occasion,
            total_generated=len(recommendations),
            recommendations=recommendations
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stylist recommendation error: {str(e)}"
        )