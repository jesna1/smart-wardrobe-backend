from pydantic import BaseModel, Field
from typing import List, Optional

class WeatherInfo(BaseModel):
    temperature_c: float
    temperature_f: float
    condition: str
    humidity: int
    wind_kph: Optional[float] = 0.0
    season_category: Optional[str] = "Summer"
    location: str
    is_fallback: bool = False

class RecommendedItem(BaseModel):
    id: int
    title: str
    image_url: Optional[str] = None
    color: Optional[str] = None

class OutfitRecommendation(BaseModel):
    outfit_id: int
    match_score: int
    ai_rationale: str
    items: List[RecommendedItem]

class StylistRecommendationResponse(BaseModel):
    weather: Optional[WeatherInfo] = None
    occasion: str
    total_generated: int
    recommendations: List[OutfitRecommendation]