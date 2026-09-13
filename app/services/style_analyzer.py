import json
import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

async def analyze_user_wardrobe_and_generate_profile(wardrobe_items: list[dict]) -> dict:
    """Analyzes user's uploaded wardrobe items to extract color palette & style archetype."""
    
    prompt = f"""
    Analyze the following list of wardrobe items and extract the user's overall personal style profile.
    Wardrobe Items: {json.dumps(wardrobe_items)}
    
    Return ONLY a valid JSON object matching this schema:
    {{
      "style_archetype": "string describing overall style (e.g., Executive Formal & Traditional Fusion)",
      "palette_name": "string naming the dominant palette (e.g., Deep Jewel & Warm Earth Tones)",
      "palette_swatches": ["#HEX1", "#HEX2", "#HEX3", "#HEX4"],
      "preferred_styles": ["Category/Item 1", "Category/Item 2", "Category/Item 3"]
    }}
    """
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = await model.generate_content_async(
        prompt, 
        generation_config={"response_mime_type": "application/json"}
    )
    
    return json.loads(response.text)