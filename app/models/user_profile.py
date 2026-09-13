# app/models/user_profile.py
from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    role = Column(String, default="Senior Developer")
    location = Column(String, default="Doha, Qatar")

    # Personal Attributes for AI Styling
    skin_type = Column(String, default="Combination")  # e.g., Sensitive, Dry, Combination
    skin_undertone = Column(String, default="Warm")     # Warm, Cool, Neutral
    seasonal_color_type = Column(String, default="Deep Autumn") # Deep Autumn, Cool Winter, Light Spring, etc.
    body_shape = Column(String, default="Hourglass")    # Hourglass, Rectangle, Pear, Inverted Triangle, Apple

    # AI Generated Styling Results
    style_archetype = Column(String, default="Executive Formal & Traditional Fusion")
    palette_name = Column(String, default="Rich Oxblood & Deep Earth Palette")
    palette_swatches = Column(JSON, default=["#4A0E17", "#800020", "#2D4A3E", "#B87333"])
    preferred_styles = Column(JSON, default=["Kasavu Sarees", "Silk Sarees", "Structured Blazers"])
    body_shape_tips = Column(JSON, default=[
        "Structured blazers with defined waistlines",
        "Belted sarees to highlight natural symmetry",
        "A-line and wrap skirts"
    ])

    user = relationship("User", back_populates="profile")