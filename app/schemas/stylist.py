from pydantic import BaseModel, Field
from typing import List, Optional

class WeatherInfo(BaseModel):
    temperature_c: float
    temperature_f: Optional[float] = None
    condition: str
    humidity: int
    wind_kph: Optional[float] = 0.0
    season_category: Optional[str] = "Summer"
    location: str
    icon_code: Optional[str] = "01d"
    is_fallback: bool = False

class RecommendedItem(BaseModel):
    id: int
    title: str
    category: str = "general"
    image_url: Optional[str] = None
    color: Optional[str] = None

class OutfitRecommendation(BaseModel):
    outfit_id: int
    title: str = "AI Curated Look"
    occasion: str = "Work"
    match_score: int
    ai_rationale: str
    is_saved: bool = False
    items: List[RecommendedItem] = []

class StylistRecommendationResponse(BaseModel):
    weather: Optional[WeatherInfo] = None
    occasion: str
    total_generated: int = 0
    recommendations: List[OutfitRecommendation] = []