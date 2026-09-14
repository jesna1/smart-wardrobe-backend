from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.attributes import flag_modified

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.wardrobe import WardrobeItem
from app.services.style_analyzer import analyze_user_style_and_aesthetics

router = APIRouter()


class UserPreferenceInput(BaseModel):
    skin_undertone: str  # e.g., "Warm", "Cool", "Neutral"
    skin_type: str  # e.g., "Combination", "Dry", "Sensitive"
    body_shape: str  # e.g., "Hourglass", "Rectangle", "Pear", "Inverted Triangle"


def format_profile_response(user: User, profile: UserProfile) -> dict:
    return {
        "name": user.full_name or "User",
        "role": profile.role or "Senior Application Developer",
        "location": profile.location or "Doha, Qatar",
        "skin_type": profile.skin_type,
        "skin_undertone": profile.skin_undertone,
        "seasonal_color_type": profile.seasonal_color_type,
        "body_shape": profile.body_shape,
        "style_archetype": profile.style_archetype,
        "palette_name": profile.palette_name,
        "palette_swatches": profile.palette_swatches or [],
        "preferred_styles": profile.preferred_styles or [],
        "body_shape_tips": profile.body_shape_tips or [],
        "wardrobe_insights": profile.wardrobe_insights or [],
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
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return format_profile_response(current_user, profile)


@router.post("/me/reanalyze-style")
async def reanalyze_user_style(
    preferences: UserPreferenceInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch user's wardrobe items for Gemini analysis context
    result = await db.execute(
        select(WardrobeItem).where(WardrobeItem.user_id == current_user.id)
    )
    wardrobe_items = result.scalars().all()
    items_payload = [
        {"category": i.category, "color": i.color, "tags": i.tags}
        for i in wardrobe_items
    ]

    # Run AI analysis engine
    analysis = await analyze_user_style_and_aesthetics(
        skin_undertone=preferences.skin_undertone,
        skin_type=preferences.skin_type,
        body_shape=preferences.body_shape,
        wardrobe_items=items_payload,
    )

    # Fetch or create user profile
    res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = res.scalars().first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    # Persist updated profile results
    profile.skin_undertone = preferences.skin_undertone
    profile.skin_type = preferences.skin_type
    profile.body_shape = preferences.body_shape
    profile.seasonal_color_type = analysis["seasonal_color_type"]
    profile.palette_name = analysis["palette_name"]
    profile.palette_swatches = analysis["palette_swatches"]
    profile.style_archetype = analysis["style_archetype"]
    profile.preferred_styles = analysis["preferred_styles"]
    profile.body_shape_tips = analysis["body_shape_tips"]
    profile.wardrobe_insights = analysis.get("wardrobe_insights", [])

    # Explicitly flag modified JSON columns for SQLAlchemy async tracking
    flag_modified(profile, "palette_swatches")
    flag_modified(profile, "preferred_styles")
    flag_modified(profile, "body_shape_tips")
    flag_modified(profile, "wardrobe_insights")

    await db.commit()
    await db.refresh(profile)

    return format_profile_response(current_user, profile)