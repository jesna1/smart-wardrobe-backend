import json
import io
import asyncio
from typing import Dict, Any
from PIL import Image
from google import genai
from app.core.config import settings


class AIVisionService:
    def __init__(self):
        invalid_keys = {"", "your-gemini-api-key", "your-actual-gemini-api-key-here"}
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() not in invalid_keys:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False

    async def analyze_garment_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyzes raw garment image bytes and returns structured AI metadata.
        Falls back to default values if Gemini is disabled or fails.
        """
        if not self.enabled or not self.client:
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
                self.client.models.generate_content,
                model="gemini-2.5-flash",
                contents=[image, prompt],
            )

            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.split("```", 1)[1].rsplit("```", 1)[0].strip()

            parsed = json.loads(raw_text)
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
            "formality": "Casual",
        }


ai_vision_service = AIVisionService()