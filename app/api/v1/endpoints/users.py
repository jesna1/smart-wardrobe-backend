from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.wardrobe import WardrobeItem
from app.services.style_analyzer import analyze_user_style_and_aesthetics

router = APIRouter()


class UserPreferenceInput(BaseModel):
    skin_undertone: str
    skin_type: str
    body_shape: str


def format_profile_response(user: User, profile: UserProfile) -> dict:
    return {
        "name": getattr(user, "full_name", None) or getattr(user, "name", "User"),
        "role": getattr(profile, "role", None) or "Senior Application Developer",
        "location": getattr(profile, "location", None) or "Doha, Qatar",
        "skin_type": getattr(profile, "skin_type", None),
        "skin_undertone": getattr(profile, "skin_undertone", None),
        "seasonal_color_type": getattr(profile, "seasonal_color_type", None),
        "body_shape": getattr(profile, "body_shape", None),
        "style_archetype": getattr(profile, "style_archetype", None),
        "palette_name": getattr(profile, "palette_name", None),
        "palette_swatches": getattr(profile, "palette_swatches", None) or [],
        "preferred_styles": getattr(profile, "preferred_styles", None) or [],
        "body_shape_tips": getattr(profile, "body_shape_tips", None) or [],
        "wardrobe_insights": getattr(profile, "wardrobe_insights", None) or [],
    }


@router.get("/me/profile")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalars().first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found.",
        )

    return format_profile_response(current_user, profile)


@router.post("/me/reanalyze-style")
async def reanalyze_user_style(
    preferences: UserPreferenceInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Eager-load category relationship to prevent MissingGreenlet async lazy-load exceptions
    result = await db.execute(
        select(WardrobeItem)
        .options(selectinload(WardrobeItem.category))
        .where(WardrobeItem.user_id == current_user.id)
    )
    wardrobe_items = result.scalars().all()

    items_payload = []
    for item in wardrobe_items:
        category_val = ""
        if hasattr(item, "category") and item.category:
            category_val = getattr(item.category, "name", str(item.category))

        tags_val = getattr(item, "ai_tags", None) or getattr(item, "tags", [])

        items_payload.append(
            {
                "category": category_val,
                "color": getattr(item, "color", "") or "",
                "tags": tags_val,
            }
        )

    try:
        analysis = await analyze_user_style_and_aesthetics(
            skin_undertone=preferences.skin_undertone,
            skin_type=preferences.skin_type,
            body_shape=preferences.body_shape,
            wardrobe_items=items_payload,
        )
        if not isinstance(analysis, dict):
            raise ValueError("AI analysis engine output is not a valid dictionary.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Style re-analysis engine failed: {str(e)}",
        )

    res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = res.scalars().first()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    profile.skin_undertone = preferences.skin_undertone
    profile.skin_type = preferences.skin_type
    profile.body_shape = preferences.body_shape
    profile.seasonal_color_type = analysis.get("seasonal_color_type", "Deep Autumn")
    profile.palette_name = analysis.get("palette_name", "Warm Earth Tones")
    profile.palette_swatches = analysis.get("palette_swatches", [])
    profile.style_archetype = analysis.get("style_archetype", "Classic Elegant")
    profile.preferred_styles = analysis.get("preferred_styles", [])
    profile.body_shape_tips = analysis.get("body_shape_tips", [])
    profile.wardrobe_insights = analysis.get("wardrobe_insights", [])

    await db.commit()
    await db.refresh(profile)

    return format_profile_response(current_user, profile)