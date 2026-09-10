from pydantic import BaseModel
from typing import List, Optional

class OutfitRecommendation(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    items: List[str] = []

class StylistRecommendationResponse(BaseModel):
    status: str
    occasion: str
    recommendations: List[OutfitRecommendation] = []