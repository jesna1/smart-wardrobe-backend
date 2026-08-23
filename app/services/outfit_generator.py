import itertools
import json
import asyncio
from typing import List, Dict, Any, Optional
import google.generativeai as genai

from app.models.wardrobe import WardrobeItem
from app.services.color_theory import calculate_color_harmony
from app.core.config import settings


class OutfitGeneratorService:
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
    def generate_outfits(
        cls, 
        items: List[WardrobeItem], 
        temp_celsius: float, 
        occasion: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        usable_items = cls.filter_by_weather(items, temp_celsius)
        usable_items = cls.filter_by_occasion(usable_items, occasion)

        tops, bottoms, shoes, outerwear = [], [], [], []

        for item in usable_items:
            cat_id = item.category_id or 0
            cat_name = item.category.name.lower() if getattr(item, "category", None) else ""
            title = (item.title or "").lower()

            if cat_id == 1 or cat_name in ["tops", "shirts", "t-shirts"] or any(k in title for k in ["shirt", "t-shirt", "top", "blouse"]):
                tops.append(item)
            elif cat_id == 2 or cat_name in ["bottoms", "pants", "jeans", "shorts", "skirts"] or any(k in title for k in ["pants", "jeans", "trousers", "skirt"]):
                bottoms.append(item)
            elif cat_id == 3 or cat_name in ["shoes", "footwear"] or any(k in title for k in ["shoes", "sneakers", "boots", "loafers"]):
                shoes.append(item)
            elif cat_id == 4 or cat_name in ["outerwear", "jackets"] or any(k in title for k in ["jacket", "coat", "blazer", "cardigan"]):
                outerwear.append(item)

        # Fallback to all items if filtered sets are missing essentials
        if not tops or not bottoms:
            for item in items:
                cat_id = item.category_id or 0
                cat_name = item.category.name.lower() if getattr(item, "category", None) else ""
                title = (item.title or "").lower()
                if (cat_id == 1 or cat_name in ["tops", "shirts"] or "top" in title) and item not in tops:
                    tops.append(item)
                elif (cat_id == 2 or cat_name in ["bottoms", "pants"] or "pants" in title) and item not in bottoms:
                    bottoms.append(item)

        if not tops or not bottoms:
            return []

        if not shoes:
            shoes = [None]

        needs_outerwear = temp_celsius < 18.0 and len(outerwear) > 0
        layers = outerwear if needs_outerwear else [None]

        candidate_outfits = []

        for top, bottom, shoe, layer in itertools.product(tops, bottoms, shoes, layers):
            c_top = top.color or "white"
            c_bottom = bottom.color or "black"
            c_shoe = shoe.color if shoe and shoe.color else "black"

            score_tb = calculate_color_harmony(c_top, c_bottom)
            score_bs = calculate_color_harmony(c_bottom, c_shoe) if shoe else 0.8
            score_ts = calculate_color_harmony(c_top, c_shoe) if shoe else 0.8

            total_score = (score_tb * 0.5) + (score_bs * 0.25) + (score_ts * 0.25)

            if layer:
                c_layer = layer.color or "navy"
                total_score = (total_score * 0.7) + (calculate_color_harmony(c_layer, c_top) * 0.3)

            match_pct = round(total_score * 100, 1)

            candidate_outfits.append({
                "score": match_pct,
                "top": top,
                "bottom": bottom,
                "shoes": shoe,
                "outerwear": layer,
                "ai_rationale": f"High color harmony match ({match_pct}%) selected for {temp_celsius}°C weather."
            })

        candidate_outfits.sort(key=lambda x: x["score"], reverse=True)
        return candidate_outfits[:limit]