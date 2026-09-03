import asyncio
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import cloudinary
import cloudinary.uploader

from app.core.database import get_db
from app.models.wardrobe import WardrobeItem, Category
from app.models.user import User
from app.api.deps import get_current_user
from app.services.ai_vision_service import ai_vision_service
from app.core.config import settings

router = APIRouter()

# Configure Cloudinary if API keys exist
if getattr(settings, "CLOUDINARY_CLOUD_NAME", None):
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


@router.post("/items/upload", status_code=status.HTTP_201_CREATED)
async def upload_wardrobe_item(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    color: Optional[str] = Form(None),
    season: Optional[str] = Form(None),
    occasion: Optional[str] = Form(None),
    remove_bg: Optional[bool] = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Uploads a wardrobe item, attaches it to current_user, runs Gemini AI auto-tagging,
    stores image via Cloudinary (non-blocking), and saves metadata to DB.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 1. Gemini AI Auto-Tagging
    ai_tags = {}
    if getattr(ai_vision_service, "enabled", False):
        try:
            ai_tags = await ai_vision_service.analyze_clothing_image(file_bytes)
        except Exception as e:
            print(f"⚠️ [AI Vision Warning] Tagging failed: {e}")

    # 2. Cloudinary Upload (Executed off main thread to prevent event-loop blocking)
    image_url = ""
    try:
        if getattr(settings, "CLOUDINARY_CLOUD_NAME", None):
            upload_options = {"folder": "smart_wardrobe/items"}
            if remove_bg:
                upload_options["background_removal"] = "cloudinary_ai"

            # Use asyncio.to_thread for synchronous Cloudinary call
            upload_result = await asyncio.to_thread(
                cloudinary.uploader.upload,
                file_bytes,
                **upload_options
            )
            image_url = upload_result.get("secure_url", "")
        else:
            image_url = "https://res.cloudinary.com/demo/image/upload/sample.jpg"
    except Exception as e:
        print(f"⚠️ [Cloudinary Warning] Upload failed: {e}")
        image_url = "https://res.cloudinary.com/demo/image/upload/sample.jpg"

    # 3. Resolve item attributes
    detected_cat = ai_tags.get("category", "Uncategorized")
    final_color = color or ai_tags.get("color") or "Unknown"
    final_season = season or ai_tags.get("season") or "All-Season"
    final_occasion = occasion or ai_tags.get("occasion") or "Casual"
    final_title = title or ai_tags.get("title") or f"{final_color.title()} {detected_cat.title()}"

    # Sanitize category_id (Treat 0 or negative values as None)
    db_category_id = category_id if (category_id and category_id > 0) else None

    # Resolve or create Category dynamically
    if db_category_id is None:
        cat_stmt = select(Category).where(Category.name.ilike(detected_cat))
        cat_res = await db.execute(cat_stmt)
        existing_cat = cat_res.scalars().first()

        if existing_cat:
            db_category_id = existing_cat.id
        else:
            new_cat = Category(name=detected_cat.title())
            db.add(new_cat)
            await db.flush()
            db_category_id = new_cat.id

    # 4. Save WardrobeItem linked to current_user.id
    item = WardrobeItem(
        title=final_title,
        image_url=image_url,
        category_id=db_category_id,
        color=final_color,
        season=final_season,
        occasion=final_occasion,
        user_id=current_user.id,
        ai_tags=json.dumps(ai_tags) if ai_tags else None,
    )

    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Fetch item with Category relationship eagerly loaded
    stmt = (
        select(WardrobeItem)
        .options(selectinload(WardrobeItem.category))
        .where(WardrobeItem.id == item.id)
    )
    res = await db.execute(stmt)
    full_item = res.scalars().first()

    return {
        "id": full_item.id,
        "title": full_item.title,
        "image_url": full_item.image_url,
        "color": full_item.color,
        "season": full_item.season,
        "occasion": full_item.occasion,
        "category_id": full_item.category_id,
        "category": {
            "id": full_item.category.id,
            "name": full_item.category.name
        } if full_item.category else None,
        "ai_detected": ai_tags,
    }


@router.get("/items")
async def get_wardrobe_items(
    category_id: Optional[int] = None,
    color: Optional[str] = None,
    season: Optional[str] = None,
    occasion: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves user's wardrobe items filtered by user_id and optional query parameters.
    """
    stmt = (
        select(WardrobeItem)
        .options(selectinload(WardrobeItem.category))
        .where(WardrobeItem.user_id == current_user.id)
    )

    if category_id and category_id > 0:
        stmt = stmt.where(WardrobeItem.category_id == category_id)
    if color:
        stmt = stmt.where(WardrobeItem.color.ilike(f"%{color}%"))
    if season:
        stmt = stmt.where(WardrobeItem.season.ilike(f"%{season}%"))
    if occasion:
        stmt = stmt.where(WardrobeItem.occasion.ilike(f"%{occasion}%"))

    result = await db.execute(stmt)
    items = result.scalars().all()

    return [
        {
            "id": item.id,
            "title": item.title,
            "image_url": item.image_url,
            "color": item.color,
            "season": item.season,
            "occasion": item.occasion,
            "category_id": item.category_id,
            "category": {
                "id": item.category.id,
                "name": item.category.name
            } if item.category else None,
        }
        for item in items
    ]


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wardrobe_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes a wardrobe item by ID for the logged-in user.
    """
    stmt = select(WardrobeItem).where(
        WardrobeItem.id == item_id, 
        WardrobeItem.user_id == current_user.id
    )
    result = await db.execute(stmt)
    item = result.scalars().first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Wardrobe item not found."
        )

    await db.delete(item)
    await db.commit()
    return None