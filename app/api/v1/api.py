from fastapi import APIRouter
from app.api.v1.endpoints import auth, wardrobe, outfits, seed, stylist

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(wardrobe.router, prefix="/wardrobe", tags=["Wardrobe"])
api_router.include_router(outfits.router, prefix="/outfits", tags=["Outfits"])
api_router.include_router(seed.router, prefix="/dev", tags=["Developer Services"])
api_router.include_router(stylist.router, prefix="/stylist", tags=["Stylist AI"])