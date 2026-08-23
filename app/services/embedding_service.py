import math
from typing import List

class EmbeddingService:
    @staticmethod
    async def extract_image_embedding(image_bytes: bytes) -> List[float]:
        """
        Simulates Fashion-CLIP 512-dimension vector feature extraction.
        In production, pass image_bytes to a loaded PyTorch CLIP model or remote inference endpoint.
        """
        # Generate normalized 512-float vector based on payload length
        seed = len(image_bytes)
        raw_vector = [math.sin(i + seed) for i in range(512)]
        
        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in raw_vector))
        normalized_vector = [x / norm for x in raw_vector]
        
        return normalized_vector

embedding_service = EmbeddingService()
