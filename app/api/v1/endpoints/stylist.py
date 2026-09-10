import itertools
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.wardrobe import WardrobeItem
from app.models.outfit import OutfitHistory  # Track worn OOTD
from app.schemas.stylist import StylistRecommendationResponse, OutfitRecommendation

router = APIRouter()

@router.get("/recommendations", response_model=StylistRecommendationResponse)
async def get_stylist_recommendations(
    occasion: str = Query("Work", description="Target occasion"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Get today's Outfit of the Day (OOTD) item IDs to exclude them
        today_ootd = db.query(OutfitHistory).filter(
            OutfitHistory.user_id == current_user.id,
            OutfitHistory.is_ootd == True
        ).first()

        excluded_item_ids = set(today_ootd.item_ids) if today_ootd else set()

        # 2. Fetch available wardrobe items for the current user
        available_items = db.query(WardrobeItem).filter(
            WardrobeItem.user_id == current_user.id,
            WardrobeItem.is_archived == False,
            ~WardrobeItem.id.in_(excluded_item_ids) if excluded_item_ids else True
        ).all()

        if not available_items:
            return {
                "status": "success",
                "occasion": occasion,
                "recommendations": []
            }

        # 3. Categorize items by occasion and type
        tops = [item for item in available_items if item.category in ["top", "shirt", "blouse"] and occasion.lower() in [o.lower() for o in item.occasions]]
        bottoms = [item for item in available_items if item.category in ["bottom", "pants", "skirt", "trousers"] and occasion.lower() in [o.lower() for o in item.occasions]]
        shoes = [item for item in available_items if item.category in ["footwear", "shoes"] and occasion.lower() in [o.lower() for o in item.occasions]]

        # Fallback to general occasion items if specific match count is low
        if not tops:
            tops = [i for i in available_items if i.category in ["top", "shirt", "blouse"]]
        if not bottoms:
            bottoms = [i for i in available_items if i.category in ["bottom", "pants", "skirt", "trousers"]]
        if not shoes:
            shoes = [i for i in available_items if i.category in ["footwear", "shoes"]]

        # 4. Generate dynamic outfit combinations
        recommendations: List[OutfitRecommendation] = []
        combo_count = 0

        for top, bottom, shoe in itertools.product(tops, bottoms, shoes):
            if combo_count >= 3:  # Limit top recommendations
                break

            # Simple heuristic match score calculation
            match_score = 85
            if top.color_family == bottom.color_family:
                match_score += 5
            if occasion.lower() in [o.lower() for o in top.occasions]:
                match_score += 5

            recommendations.append(
                OutfitRecommendation(
                    id=f"rec_{top.id}_{bottom.id}_{shoe.id}",
                    title=f"{occasion} Ensemble #{combo_count + 1}",
                    description=f"Featuring {top.title} paired with {bottom.title} and {shoe.title}.",
                    image_url=top.image_url,
                    items=[top.title, bottom.title, shoe.title]
                )
            )
            combo_count += 1

        return {
            "status": "success",
            "occasion": occasion,
            "recommendations": recommendations
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )