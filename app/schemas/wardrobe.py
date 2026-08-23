from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str


class CategoryResponse(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class WardrobeItemBase(BaseModel):
    title: str
    color: Optional[str] = None
    season: Optional[str] = None
    occasion: Optional[str] = None  # <--- ADD THIS
    image_url: Optional[str] = None
    category_id: Optional[int] = None


class WardrobeItemUpdate(BaseModel):
    title: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    occasion: Optional[str] = None  # <--- ADD THIS
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    embedding: Optional[List[float]] = None


class WardrobeItemCreate(WardrobeItemBase):
    embedding: Optional[List[float]] = None





class WardrobeItemResponse(WardrobeItemBase):
    id: int
    created_at: Optional[datetime] = None  # <--- Changed from datetime to Optional[datetime]
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class VectorSearchQuery(BaseModel):
    vector: List[float] = Field(..., description="512-dimensional embedding vector")
    limit: int = Field(default=5, ge=1, le=50)