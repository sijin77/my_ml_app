import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.ml_queue_request_service import MLRequestOrchestratorService
from schemas.mlmodel import MLModelCreate, MLModelRead
from services.mlmodel_service import MLModelService
from schemas.request_history import (
    RequestHistoryCreate,
    RequestHistoryRead,
)
from services.request_history_service import RequestHistoryService
from services.dependencies import (
    get_ml_orchestrator_service,
    get_mlmodel_service,
    get_request_history_service,
    get_queue_service,
)

router = APIRouter(prefix="/ml-models", tags=["ml model"])


@router.post("/model", response_model=MLModelRead)
async def create_model(
    model_data: MLModelCreate,
    mlmodel_service: MLModelService = Depends(get_mlmodel_service),
):
    try:
        return await mlmodel_service.create_model(model_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/predict", response_model=RequestHistoryRead)
async def create_prediction_request(
    request: RequestHistoryCreate,
    orchestrator: MLRequestOrchestratorService = Depends(get_ml_orchestrator_service),
):
    """
    Отправляет запрос на предсказание через оркестратор
    """
    try:
        return await orchestrator.process_prediction_request(
            user_id=request.user_id,
            model_id=request.model_id,
            input_data=request.input_data,
            request_type=request.request_type,
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/user/{user_id}/prediction", response_model=List[RequestHistoryRead])
async def get_user_requests(
    user_id: int,
    request_service: RequestHistoryService = Depends(get_request_history_service),
):
    try:
        return await request_service.get_user_requests(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
