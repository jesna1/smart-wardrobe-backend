from fastapi import APIRouter, Query, HTTPException, status
from app.schemas.stylist import StylistRecommendationResponse

router = APIRouter()

@router.get("/recommendations", response_model=StylistRecommendationResponse)
async def get_stylist_recommendations(
    occasion: str = Query("Work", description="Target occasion (e.g. Work, Casual, Formal)")
):
    try:
        return {
            "status": "success",
            "occasion": occasion,
            "recommendations": []
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )