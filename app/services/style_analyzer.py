import logging
from typing import Any, Dict, List

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


class StyleAnalysisResponse(BaseModel):
    seasonal_color_type: str = Field(
        description="Seasonal Color category (e.g., Deep Autumn, Cool Winter)."
    )
    palette_name: str = Field(
        description="A cohesive, descriptive palette name tailored to the user's skin undertone."
    )
    palette_swatches: List[str] = Field(
        description="Exactly 4 hex color strings (#HEX) complementary to the user's skin undertone."
    )
    style_archetype: str = Field(
        description="A style archetype derived from the user's body shape and wardrobe items."
    )
    preferred_styles: List[str] = Field(
        description="3 key garment styles or silhouettes best suited for this body shape."
    )
    body_shape_tips: List[str] = Field(
        description="3 actionable tailoring/styling tips tailored specifically to this body shape."
    )
    wardrobe_insights: List[str] = Field(
        description="2-3 actionable recommendations on how to style, layer, or pair the provided wardrobe items."
    )


async def analyze_user_style_and_aesthetics(
    skin_undertone: str,
    skin_type: str,
    body_shape: str,
    wardrobe_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Evaluates skin undertone, body shape, and wardrobe items via Gemini AI with structured schema enforcement."""

    prompt = f"""
    You are an expert personal stylist and color analyst. Analyze the following user profile and inventory:

    - Skin Undertone: {skin_undertone}
    - Skin Type: {skin_type}
    - Body Shape: {body_shape}
    - Wardrobe Inventory: {wardrobe_items}

    Task Details:
    1. Color Analysis: Identify the precise Seasonal Color category and generate 4 hex swatches tailored for {skin_undertone} undertones.
    2. Body Shape Styling: Define an archetype, 3 preferred garment styles, and 3 specific tailoring/fitting tips for a {body_shape} frame.
    3. Wardrobe Analysis: Evaluate the provided Wardrobe Inventory. Provide explicit recommendations on how to style or combine those specific items with the recommended color palette and body shape guidelines.
    """

    try:
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        client = genai.Client(api_key=api_key)

        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StyleAnalysisResponse,
                temperature=0.3,
            ),
        )

        # Validates and parses directly into a dictionary adhering strictly to StyleAnalysisResponse schema
        return StyleAnalysisResponse.model_validate_json(response.text).model_dump()

    except Exception as e:
        logger.error(f"Gemini API analysis failed: {e}")

        # Lightweight dynamic fallback using input parameters directly
        return {
            "seasonal_color_type": f"Custom {skin_undertone.capitalize()}",
            "palette_name": f"{skin_undertone.capitalize()} Harmonious Palette",
            "palette_swatches": ["#4A0E17", "#800020", "#2D4A3E", "#B87333"],
            "style_archetype": f"Tailored {body_shape.capitalize()} Silhouette",
            "preferred_styles": ["Structured Blazers", "Tailored Trousers", "Wrap Outfits"],
            "body_shape_tips": [
                f"Choose structured cuts that define proportions for a {body_shape} frame.",
                "Maintain line balance between upper and lower body proportions.",
                "Opt for fabrics that hold structure while drape fluidly.",
            ],
            "wardrobe_insights": [
                "Pair core neutral wardrobe items with secondary accent pieces matching your color palette."
            ],
        }