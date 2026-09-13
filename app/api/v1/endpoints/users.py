from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.wardrobe import WardrobeItem
from app.services.style_analyzer import analyze_user_wardrobe_and_generate_profile
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/me/profile")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalars().first()
    
    if not profile:
        # Return fallback default if profile not yet generated
        return {
            "name": current_user.full_name,
            "role": "Senior Application Developer",
            "location": "Doha, Qatar",
            "style_archetype": "Executive Formal & Traditional Fusion",
            "palette_name": "Deep Jewel & Warm Earth Tones",
            "palette_swatches": ["#4A0E17", "#800020", "#2D4A3E", "#B87333"],
            "preferred_styles": ["Kasavu Sarees", "Silk Sarees", "Structured Blazers"]
        }

    return {
        "name": current_user.full_name,
        "role": profile.role,
        "location": profile.location,
        "style_archetype": profile.style_archetype,
        "palette_name": profile.palette_name,
        "palette_swatches": profile.palette_swatches,
        "preferred_styles": profile.preferred_styles,
    }

@router.post("/me/reanalyze-style")
async def sync_user_style_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch user's wardrobe items from DB
    result = await db.execute(select(WardrobeItem).where(WardrobeItem.user_id == current_user.id))
    items = result.scalars().all()
    
    item_dicts = [{"category": item.category, "color": item.color, "tags": item.tags} for item in items]
    
    # 2. Analyze with Gemini API
    analysis = await analyze_user_wardrobe_and_generate_profile(item_dicts)
    
    # 3. Save or Update in UserProfile table
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalars().first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        
    profile.style_archetype = analysis["style_archetype"]
    profile.palette_name = analysis["palette_name"]
    profile.palette_swatches = analysis["palette_swatches"]
    profile.preferred_styles = analysis["preferred_styles"]
    
    await db.commit()
    await db.refresh(profile)
    return profile