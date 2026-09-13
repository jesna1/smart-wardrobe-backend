# app/services/style_analyzer.py
import json
import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

async def analyze_user_style_and_aesthetics(
    skin_undertone: str,
    skin_type: str,
    body_shape: str,
    wardrobe_items: list[dict]
) -> dict:
    """Uses Gemini AI to evaluate skin undertone, body shape, and wardrobe items

    to derive seasonal color palette and silhouette guidelines.
    """

    prompt = f"""
    Perform an expert AI color analysis and body shape styling analysis for a user with these parameters:
    - Skin Undertone: {skin_undertone}
    - Skin Type: {skin_type}
    - Body Shape: {body_shape}
    - Uploaded Wardrobe Inventory: {json.dumps(wardrobe_items)}

    Analyze:
    1. Determine the exact Seasonal Color Analysis (e.g., Deep Autumn, Soft Summer, Bright Spring, Clear Winter) that harmonizes with a {skin_undertone} undertone.
    2. Generate 4 complimentary hex color swatches (#HEX format) that flatter this color analysis.
    3. Determine the best Style Archetype and 3 specific garment silhouette tips tailored for a {body_shape} body shape.

    Return ONLY a JSON response matching this schema:
    {{
      "seasonal_color_type": "string (e.g. Deep Autumn)",
      "palette_name": "string naming the palette",
      "palette_swatches": ["#HEX1", "#HEX2", "#HEX3", "#HEX4"],
      "style_archetype": "string (e.g. Executive Formal & Traditional Fusion)",
      "preferred_styles": ["Item/Garment 1", "Item/Garment 2", "Item/Garment 3"],
      "body_shape_tips": ["Tip 1 for body shape", "Tip 2 for body shape", "Tip 3 for body shape"]
    }}
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = await model.generate_content_async(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )

    return json.loads(response.text)