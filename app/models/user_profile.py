from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    role = Column(String, default="Senior Application Developer")
    location = Column(String, default="Doha, Qatar")

    # Personal Attributes for AI Styling
    skin_type = Column(String, default="Combination")
    skin_undertone = Column(String, default="Warm")
    seasonal_color_type = Column(String, default="Deep Autumn")
    body_shape = Column(String, default="Hourglass")

    # AI Generated Styling Results
    style_archetype = Column(String, default="Executive Formal & Traditional Fusion")
    palette_name = Column(String, default="Rich Oxblood & Deep Earth Palette")
    palette_swatches = Column(
        JSON, default=lambda: ["#4A0E17", "#800020", "#2D4A3E", "#B87333"]
    )
    preferred_styles = Column(
        JSON, default=lambda: ["Kasavu Sarees", "Silk Sarees", "Structured Blazers"]
    )
    body_shape_tips = Column(
        JSON,
        default=lambda: [
            "Structured blazers with defined waistlines",
            "Belted sarees to highlight natural symmetry",
            "A-line and wrap skirts",
        ],
    )
    wardrobe_insights = Column(JSON, default=list)

    # Relationship (declared once)
    user = relationship("User", back_populates="profile")