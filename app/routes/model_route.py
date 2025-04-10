from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.mlmodel import MLModelCreate, MLModelRead
from services.mlmodel_service import MLModelService
from schemas.request_history import (
    RequestHistoryCreate,
    RequestHistoryDetailRead,
    RequestHistoryRead,
)
from services.request_history_service import RequestHistoryService
from services.dependencies import get_mlmodel_service, get_request_history_service

router = APIRouter(prefix="/ml-models", tags=["ml model"])


@router.post("/create_model", response_model=MLModelRead)
async def create_model(
    model_data: MLModelCreate,
    mlmodel_service: MLModelService = Depends(get_mlmodel_service),
):
    try:
        return await mlmodel_service.create_model(model_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/request_to_model", response_model=RequestHistoryRead)
async def create_request(
    request_data: RequestHistoryCreate,
    request_service: RequestHistoryService = Depends(get_request_history_service),
):
    try:
        return await request_service.create_request(request_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}/reqests", response_model=List[RequestHistoryRead])
async def get_user_requests(
    user_id: int,
    request_service: RequestHistoryService = Depends(get_request_history_service),
):
    try:
        return await request_service.get_user_requests(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
