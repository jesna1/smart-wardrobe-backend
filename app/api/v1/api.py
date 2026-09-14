from fastapi import APIRouter
from app.api.v1.endpoints import auth, outfits, seed, users, wardrobe

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(wardrobe.router, prefix="/wardrobe", tags=["Wardrobe"])
api_router.include_router(outfits.router, prefix="/stylist", tags=["Stylist"])
api_router.include_router(seed.router, prefix="/dev", tags=["Developer Services"])