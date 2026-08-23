from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)

    items = relationship("WardrobeItem", back_populates="category")


class WardrobeItem(Base):
    __tablename__ = "wardrobe_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    image_url = Column(String(512), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    color = Column(String(100), nullable=True)
    season = Column(String(100), nullable=True)
    occasion = Column(String(100), nullable=True)
    ai_tags = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    category = relationship("Category", back_populates="items")
    user = relationship("User", back_populates="wardrobe_items")