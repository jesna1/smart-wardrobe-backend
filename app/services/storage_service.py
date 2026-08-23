import asyncio
import os
import uuid
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from app.core.config import settings


class StorageService:
    def __init__(self):
        # Configure Cloudinary if credentials are present
        if (
            settings.CLOUDINARY_CLOUD_NAME 
            and settings.CLOUDINARY_API_KEY 
            and settings.CLOUDINARY_API_SECRET
        ):
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True,
            )
            self.use_cloudinary = True
        else:
            self.use_cloudinary = False
            self.upload_dir = "uploads"
            os.makedirs(self.upload_dir, exist_ok=True)

    async def upload_image(self, file: UploadFile, folder: str = "wardrobe") -> str:
        """
        Uploads an image file to Cloudinary or falls back to local storage.
        Returns the accessible HTTPS or local file URL string.
        """
        file_bytes = await file.read()

        if self.use_cloudinary:
            # Run blocking Cloudinary upload call in a thread pool
            result = await asyncio.to_thread(
                cloudinary.uploader.upload,
                file_bytes,
                folder=f"aura_wardrobe/{folder}",
                resource_type="image",
            )
            return result.get("secure_url")
        else:
            # Fallback: Save to local uploads folder
            extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
            filename = f"{uuid.uuid4().hex}.{extension}"
            file_path = os.path.join(self.upload_dir, filename)

            with open(file_path, "wb") as f:
                f.write(file_bytes)

            return f"/uploads/{filename}"


storage_service = StorageService()