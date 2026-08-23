from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.wardrobe import WardrobeItemResponse

class OutfitBase(BaseModel):
    name: str
    description: Optional[str] = None
    occasion: Optional[str] = None

class OutfitCreate(OutfitBase):
    item_ids: List[int]

class OutfitGenerateRequest(BaseModel):
    anchor_item_id: int = Field(..., description="ID of the item around which to build the outfit")
    occasion: Optional[str] = Field("Casual", description="Target occasion for the look")
    name: Optional[str] = Field(None, description="Optional custom outfit name")

class DailyRecommendationRequest(BaseModel):
    city: str = Field(default="Doha", description="Target city for weather evaluation")
    occasion: str = Field(default="Workwear", description="Target occasion (e.g. Workwear, Casual, Formal)")

class OutfitResponse(OutfitBase):
    id: int
    created_at: datetime
    items: List[WardrobeItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
