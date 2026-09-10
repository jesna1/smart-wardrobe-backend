from pydantic import BaseModel
from typing import List, Optional

class OutfitItemDetail(BaseModel):
    id: str
    title: str
    category: str
    image_url: Optional[str] = None

class OutfitRecommendation(BaseModel):
    id: str
    title: str
    ai_rationale: Optional[str] = None
    match_score: int = 90
    image_url: Optional[str] = None
    items: List[OutfitItemDetail] = []
    is_saved: bool = False

class StylistRecommendationResponse(BaseModel):
    status: str
    occasion: str
    recommendations: List[OutfitRecommendation] = []