import json
import logging
import itertools
from typing import List, Dict, Any, Optional
from sqlalchemy.orm.attributes import instance_state

from google import genai
from google.genai import types

from app.models.wardrobe import WardrobeItem
from app.services.color_theory import calculate_color_harmony
from app.core.config import settings

logger = logging.getLogger(__name__)


class OutfitGeneratorService:
    @staticmethod
    def _get_category_name(item: WardrobeItem) -> str:
        """Safely retrieves category name without triggering SQLAlchemy lazy-loading."""
        try:
            state = instance_state(item)
            if "category" in state.dict and item.category is not None:
                return (item.category.name or "").lower()
        except Exception:
            pass
        return ""

    @classmethod
    def classify_item(cls, item: WardrobeItem) -> str:
        """
        Classifies clothing items into one_piece, tops, bottoms, shoes, or outerwear.
        """
        title = (item.title or "").lower()
        cat_name = cls._get_category_name(item)
        cat_id = item.category_id or 0

        # One-Piece / Draped Garments (Saree, Dress, Jumpsuit, etc.)
        one_piece_keywords = ["saree", "sari", "dress", "gown", "jumpsuit", "romper", "anarkali", "lehenga", "kaftan"]
        if cat_id == 5 or cat_name in ["dresses", "sarees", "one-piece"] or any(k in title for k in one_piece_keywords):
            return "one_piece"

        # Outerwear
        outerwear_keywords = ["jacket", "coat", "blazer", "cardigan", "shrug", "shawl", "dupatta", "trench"]
        if cat_id == 4 or cat_name in ["outerwear", "jackets"] or any(k in title for k in outerwear_keywords):
            return "outerwear"

        # Footwear
        shoe_keywords = ["shoes", "sneakers", "boots", "loafers", "heels", "sandals", "flats", "footwear"]
        if cat_id == 3 or cat_name in ["shoes", "footwear"] or any(k in title for k in shoe_keywords):
            return "shoes"

        # Bottoms
        bottom_keywords = ["pants", "jeans", "trousers", "skirt", "shorts", "palazzo", "leggings", "chinos", "pant"]
        if cat_id == 2 or cat_name in ["bottoms", "pants", "jeans"] or any(k in title for k in bottom_keywords):
            return "bottoms"

        # Default to Tops
        return "tops"

    @staticmethod
    def filter_by_weather(items: List[WardrobeItem], temp_celsius: float) -> List[WardrobeItem]:
        filtered = []
        for item in items:
            season = (item.season or "").lower()
            if temp_celsius >= 28.0 and season in ["winter", "heavy"]:
                continue
            elif temp_celsius <= 15.0 and season in ["summer", "sheer"]:
                continue
            filtered.append(item)
        return filtered

    @staticmethod
    def filter_by_occasion(items: List[WardrobeItem], occasion: Optional[str]) -> List[WardrobeItem]:
        if not occasion or not occasion.strip():
            return items

        target = occasion.strip().lower()
        matching = [
            item for item in items 
            if item.occasion and item.occasion.strip().lower() == target
        ]
        return matching if len(matching) >= 2 else items

    @classmethod
    async def generate_outfits(
        cls, 
        items: List[WardrobeItem], 
        temp_celsius: float, 
        occasion: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        usable_items = cls.filter_by_weather(items, temp_celsius)
        usable_items = cls.filter_by_occasion(usable_items, occasion)

        # 1. Group items into functional buckets
        buckets: Dict[str, List[WardrobeItem]] = {
            "one_piece": [], "tops": [], "bottoms": [], "shoes": [], "outerwear": []
        }
        for item in usable_items:
            bucket_key = cls.classify_item(item)
            buckets[bucket_key].append(item)

        candidates = []
        shoes_list = buckets["shoes"] or [None]
        needs_outerwear = temp_celsius < 18.0 and len(buckets["outerwear"]) > 0
        outerwear_list = buckets["outerwear"] if needs_outerwear else [None]

        # 2. Build Stream A: One-Piece Outfits (Saree/Dress + Shoes + Optional Layer)
        for piece in buckets["one_piece"]:
            for shoe, layer in itertools.product(shoes_list, outerwear_list):
                candidates.append({
                    "type": "one_piece",
                    "top": piece,
                    "bottom": None,
                    "shoes": shoe,
                    "outerwear": layer
                })

        # 3. Build Stream B: Two-Piece Outfits (Top + Bottom + Shoes + Optional Layer)
        for top, bottom in itertools.product(buckets["tops"], buckets["bottoms"]):
            for shoe, layer in itertools.product(shoes_list, outerwear_list):
                candidates.append({
                    "type": "two_piece",
                    "top": top,
                    "bottom": bottom,
                    "shoes": shoe,
                    "outerwear": layer
                })

        if not candidates:
            return []

        # Limit candidate pool sent to Gemini to max 12 items for fast latency
        evaluation_pool = candidates[:12]

        # 4. Evaluate using Gemini 2.5 Flash
        ai_results = await cls._evaluate_candidates_with_gemini(
            candidates=evaluation_pool,
            temp_celsius=temp_celsius,
            occasion=occasion or "Casual"
        )

        ai_results.sort(key=lambda x: x["score"], reverse=True)
        return ai_results[:limit]

    @classmethod
    async def _evaluate_candidates_with_gemini(
        cls, 
        candidates: List[Dict[str, Any]], 
        temp_celsius: float, 
        occasion: str
    ) -> List[Dict[str, Any]]:
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            logger.warning("GEMINI_API_KEY unset. Falling back to heuristic scoring.")
            return cls._heuristic_fallback(candidates, temp_celsius)

        try:
            client = genai.Client(api_key=api_key)

            payload_items = []
            for idx, c in enumerate(candidates, start=1):
                payload_items.append({
                    "candidate_id": idx,
                    "garment_type": c["type"],
                    "primary_item": f"{c['top'].title} (Color: {c['top'].color or 'Unknown'})",
                    "bottom_item": f"{c['bottom'].title} (Color: {c['bottom'].color or 'Unknown'})" if c["bottom"] else "None",
                    "footwear": f"{c['shoes'].title} (Color: {c['shoes'].color or 'Unknown'})" if c["shoes"] else "None",
                    "outerwear": f"{c['outerwear'].title} (Color: {c['outerwear'].color or 'Unknown'})" if c["outerwear"] else "None"
                })

            prompt = f"""
            You are an expert personal stylist. Evaluate these outfit candidates for a user in {temp_celsius}°C weather attending a '{occasion}' occasion.

            Candidates:
            {json.dumps(payload_items, indent=2)}

            Rules:
            1. Sarees, Dresses, and One-Piece garments MUST NOT be combined with bottom-wear like pants or skirts.
            2. Rate each candidate from 0 to 100 for aesthetic harmony, silhouette balance, and occasion appropriateness.
            3. Set 'is_valid' to false for incompatible items (e.g., formal blazer with gym shorts).
            4. Provide a 1-sentence personalized styling rationale for each valid outfit.

            Respond strictly in valid JSON format matching this schema:
            [
              {{
                "candidate_id": 1,
                "is_valid": true,
                "score": 90.0,
                "ai_rationale": "An elegant white saree paired with minimal footwear creates a graceful look for formal wear."
              }}
            ]
            """

            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            results = json.loads(response.text)
            eval_map = {r["candidate_id"]: r for r in results if isinstance(r, dict)}

            evaluated_outfits = []
            for idx, c in enumerate(candidates, start=1):
                eval_data = eval_map.get(idx, {})
                if eval_data.get("is_valid", True):
                    c["score"] = float(eval_data.get("score", 75.0))
                    c["ai_rationale"] = eval_data.get("ai_rationale", f"Curated outfit styled for {occasion}.")
                    evaluated_outfits.append(c)

            return evaluated_outfits if evaluated_outfits else cls._heuristic_fallback(candidates, temp_celsius)

        except Exception as e:
            logger.error(f"Gemini evaluation failed: {e}", exc_info=True)
            return cls._heuristic_fallback(candidates, temp_celsius)

    @classmethod
    def _heuristic_fallback(cls, candidates: List[Dict[str, Any]], temp_celsius: float) -> List[Dict[str, Any]]:
        evaluated = []
        for c in candidates:
            top = c["top"]
            bottom = c["bottom"]
            shoe = c["shoes"]

            c_top = top.color or "white"
            c_bottom = bottom.color if bottom else c_top
            c_shoe = shoe.color if shoe else "black"

            if bottom:
                score_tb = calculate_color_harmony(c_top, c_bottom)
                score_bs = calculate_color_harmony(c_bottom, c_shoe)
                score_ts = calculate_color_harmony(c_top, c_shoe)
                total_score = (score_tb * 0.5) + (score_bs * 0.25) + (score_ts * 0.25)
            else:
                total_score = calculate_color_harmony(c_top, c_shoe)

            match_pct = round(total_score * 100, 1)
            c["score"] = match_pct
            c["ai_rationale"] = f"Harmonious combination featuring {top.title} selected for {temp_celsius}°C weather."
            evaluated.append(c)

        return evaluated