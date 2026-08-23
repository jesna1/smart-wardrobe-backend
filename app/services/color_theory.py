from typing import Optional, List, Tuple, Dict, Any
import colorsys
import re
from typing import Tuple

NEUTRAL_HEXES = {
    "#000000", "#FFFFFF", "#808080", "#D3D3D3", 
    "#F5F5DC", "#000080", "#708090", "#696969"
}

NEUTRAL_NAMES = {"black", "white", "grey", "gray", "beige", "navy", "denim", "khaki"}

def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) != 6:
        return (128, 128, 128)
    return tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))

def is_neutral(color_str: Optional[str]) -> bool:
    if not color_str:
        return True
    color_clean = color_str.strip().lower()
    if color_clean in NEUTRAL_NAMES or color_clean in NEUTRAL_HEXES:
        return True
    return False

def calculate_color_harmony(color1: Optional[str], color2: Optional[str]) -> float:
    """Returns a score between 0.0 (clashing) and 1.0 (perfect match)."""
    if not color1 or not color2:
        return 0.7  # Default neutral score if color data is unassigned
    
    if is_neutral(color1) or is_neutral(color2):
        return 0.95  # Neutrals match almost anything

    rgb1 = hex_to_rgb(color1) if color1.startswith("#") else (100, 100, 100)
    rgb2 = hex_to_rgb(color2) if color2.startswith("#") else (200, 200, 200)

    h1, s1, v1 = colorsys.rgb_to_hsv(rgb1[0]/255.0, rgb1[1]/255.0, rgb1[2]/255.0)
    h2, s2, v2 = colorsys.rgb_to_hsv(rgb2[0]/255.0, rgb2[1]/255.0, rgb2[2]/255.0)

    hue_diff = abs(h1 - h2) * 360
    if hue_diff > 180:
        hue_diff = 360 - hue_diff

    # Direct match or Monochromatic
    if hue_diff < 15:
        return 0.9
    # Analogous (neighboring colors on wheel)
    elif 15 <= hue_diff <= 45:
        return 0.85
    # Complementary (opposite on wheel)
    elif 150 <= hue_diff <= 210:
        return 0.9
    # Clashing range
    elif 60 <= hue_diff <= 120:
        return 0.4
    
    return 0.65