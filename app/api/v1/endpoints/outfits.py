from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.wardrobe import WardrobeItem
from app.services.weather_service import weather_service
from app.services.outfit_generator import OutfitGeneratorService

router = APIRouter()


@router.get("/recommendations")
async def get_outfit_recommendations(
    lat: float = Query(25.2854, description="Latitude for weather lookup"),
    lon: float = Query(51.5310, description="Longitude for weather lookup"),
    occasion: Optional[str] = Query(None, description="Target occasion (e.g., Casual, Formal, Work)"),
    limit: int = Query(5, ge=1, le=20, description="Max number of outfit combinations"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates AI outfit recommendations based on live weather, color harmony, and target occasion.
    """
    # 1. Fetch current weather data
    weather_data = await weather_service.get_current_weather(lat, lon)
    temp_celsius = weather_data.get("temperature_c", 25.0)

    # 2. Query stored wardrobe items
    result = await db.execute(select(WardrobeItem))
    items = result.scalars().all()

    if not items:
        return {
            "weather": weather_data,
            "occasion": occasion,
            "total_generated": 0,
            "outfits": [],
            "message": "No wardrobe items found. Upload clothing items to get recommendations.",
        }

    # 3. Generate outfits scored by weather and color harmony
    generated_outfits = OutfitGeneratorService.generate_outfits(
        items=list(items),
        temp_celsius=temp_celsius,
        occasion=occasion,
        limit=limit,
    )

    formatted_outfits = []
    for idx, outfit in enumerate(generated_outfits, start=1):
        formatted_outfits.append({
            "outfit_id": idx,
            "score": outfit["score"],
            "ai_rationale": outfit["ai_rationale"],
            "items": {
                "top": {
                    "id": outfit["top"].id,
                    "title": outfit["top"].title,
                    "image_url": outfit["top"].image_url,
                    "color": outfit["top"].color,
                } if outfit.get("top") else None,
                "bottom": {
                    "id": outfit["bottom"].id,
                    "title": outfit["bottom"].title,
                    "image_url": outfit["bottom"].image_url,
                    "color": outfit["bottom"].color,
                } if outfit.get("bottom") else None,
                "shoes": {
                    "id": outfit["shoes"].id,
                    "title": outfit["shoes"].title,
                    "image_url": outfit["shoes"].image_url,
                    "color": outfit["shoes"].color,
                } if outfit.get("shoes") else None,
                "outerwear": {
                    "id": outfit["outerwear"].id,
                    "title": outfit["outerwear"].title,
                    "image_url": outfit["outerwear"].image_url,
                    "color": outfit["outerwear"].color,
                } if outfit.get("outerwear") else None,
            }
        })

    return {
        "weather": weather_data,
        "occasion": occasion,
        "total_generated": len(formatted_outfits),
        "outfits": formatted_outfits,
    }