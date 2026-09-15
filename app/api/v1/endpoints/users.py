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
    # Use getattr to safely guard against missing model columns or null values
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
    try:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == current_user.id)
        )
        profile = result.scalars().first()

        if not profile:
            # Instantiate with optional default placeholders if non-nullable
            profile = UserProfile(
                user_id=current_user.id,
                skin_type="Sensitive",
                skin_undertone="Olive",
                body_shape="Apple",
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)

        return format_profile_response(current_user, profile)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch profile: {str(e)}",
        )
@router.post("/me/reanalyze-style")
async def reanalyze_user_style(
    preferences: UserPreferenceInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Safe extraction of wardrobe items with null guards
    result = await db.execute(
        select(WardrobeItem).where(WardrobeItem.user_id == current_user.id)
    )
    wardrobe_items = result.scalars().all()
    items_payload = [
        {
            "category": getattr(i, "category", "") or "",
            "color": getattr(i, "color", "") or "",
            "tags": getattr(i, "tags", []) or [],
        }
        for i in wardrobe_items
    ]

    # Execute AI engine with exception boundary
    try:
        analysis = await analyze_user_style_and_aesthetics(
            skin_undertone=preferences.skin_undertone,
            skin_type=preferences.skin_type,
            body_shape=preferences.body_shape,
            wardrobe_items=items_payload,
        )
        if not isinstance(analysis, dict):
            raise ValueError("AI analysis returned an invalid non-dictionary payload.")
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported style preference option: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Style re-analysis engine failed: {str(e)}",
        )

    # Fetch or create user profile
    res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = res.scalars().first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    # Safe updates using dict.get() defaults
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

    # Explicitly flag modified JSON columns for SQLAlchemy tracking
    json_fields = ["palette_swatches", "preferred_styles", "body_shape_tips", "wardrobe_insights"]
    for field in json_fields:
        flag_modified(profile, field)

    await db.commit()
    await db.refresh(profile)

    return format_profile_response(current_user, profile)