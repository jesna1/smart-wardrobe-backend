from pydantic import BaseModel, Field
from typing import List, Optional

class WeatherInfo(BaseModel):
    temperature_c: float = Field(..., example=32.0)
    condition: str = Field(..., example="Sunny & Clear")
    location: str = Field(..., example="Doha, Qatar")
    humidity: int = Field(..., example=55)
    icon_code: str = Field(..., example="01d")

class RecommendedItem(BaseModel):
    id: int
    title: str
    category: str
    image_url: Optional[str] = None
    color: Optional[str] = None

class OutfitRecommendation(BaseModel):
    outfit_id: int
    title: str
    occasion: str
    match_score: int
    ai_rationale: str
    is_saved: bool = False
    items: List[RecommendedItem] = []

class StylistRecommendationResponse(BaseModel):
    status: str
    occasion: str
    weather: Optional[WeatherInfo] = None
    recommendations: List[OutfitRecommendation] = []