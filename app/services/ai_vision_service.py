import json
import io
import asyncio
from typing import Dict, Any
from PIL import Image
import google.generativeai as genai
from app.core.config import settings


class AIVisionService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            self.enabled = True
        else:
            self.enabled = False

    async def analyze_garment_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyzes raw garment image bytes and returns structured AI metadata.
        Falls back to default values if Gemini is disabled or fails.
        """
        if not self.enabled:
            return self._fallback_metadata()

        try:
            image = Image.open(io.BytesIO(image_bytes))
            prompt = """
            Analyze this clothing item photo and extract structured garment metadata.
            Return ONLY a JSON object with these exact keys:
            {
              "title": "Short descriptive name (e.g., Navy Blue Blazer)",
              "category": "Tops" | "Bottoms" | "Shoes" | "Outerwear" | "Accessories",
              "dominant_color": "color name (e.g., navy, white, beige, black, olive)",
              "season": "Summer" | "Winter" | "Spring/Autumn" | "All-Season",
              "occasion": "Casual" | "Work" | "Formal" | "Party" | "Sport",
              "formality": "Casual" | "Smart Casual" | "Formal"
            }
            """

            response = await asyncio.to_thread(
                self.model.generate_content,
                [image, prompt],
                generation_config={"response_mime_type": "application/json"}
            )

            parsed = json.loads(response.text)
            return parsed
        except Exception as e:
            print(f"[AI Vision Error] {e}")
            return self._fallback_metadata()

    def _fallback_metadata(self) -> Dict[str, Any]:
        return {
            "title": "Uploaded Item",
            "category": "Tops",
            "dominant_color": "black",
            "season": "All-Season",
            "occasion": "Casual",
            "formality": "Casual"
        }


ai_vision_service = AIVisionService()