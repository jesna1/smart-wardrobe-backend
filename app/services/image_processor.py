import io
from PIL import Image
from rembg import remove

class ImageProcessor:
    @staticmethod
    def remove_background(image_bytes: bytes) -> bytes:
        """Removes background and returns transparent PNG bytes."""
        input_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        output_image = remove(input_image)
        
        buffer = io.BytesIO()
        output_image.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()

    @staticmethod
    def extract_dominant_color(image_bytes: bytes) -> str:
        """Simple color analysis returning hex code of primary clothing color."""
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize((50, 50))
        colors = image.getcolors(maxcolors=2500)
        if not colors:
            return "#FFFFFF"
        
        # Sort by frequency and return dominant hex
        dominant = max(colors, key=lambda item: item[0])[1]
        return f"#{dominant[0]:02x}{dominant[1]:02x}{dominant[2]:02x}"