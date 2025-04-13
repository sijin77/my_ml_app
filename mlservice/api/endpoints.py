from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.dependecies import get_ml_service

router = APIRouter()


class PredictionRequest(BaseModel):
    text: str
    image_base64: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/predict")
async def predict(
    request: PredictionRequest,
    ml_service=Depends(get_ml_service),
):
    try:
        return await ml_service.predict(
            text=request.text,
            image_base64=request.image_base64,
            session_id=request.session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
