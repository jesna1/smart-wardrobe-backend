from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    role = Column(String, default="Developer")
    location = Column(String, default="Doha, Qatar")
    style_archetype = Column(String, default="Executive Formal")
    palette_name = Column(String, default="Deep Jewel Tones")
    palette_swatches = Column(JSON, default=["#4A0E17", "#800020", "#2D4A3E", "#B87333"])  # Hex strings
    preferred_styles = Column(JSON, default=["Blazers", "Silk Sarees", "Kasavu Sarees"])

    user = relationship("User", back_populates="profile")