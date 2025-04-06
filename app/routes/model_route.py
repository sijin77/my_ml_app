from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.mlmodel import MLModelCreate, MLModelDetailRead
from services.dependencies import get_async_session
from services.mlmodel_service import MLModelService
from schemas.mlmodel_settings import MLModelSettingCreate, MLModelSettingDetailRead
from services.mlmodel_settings_service import MLModelSettingsService
from schemas.request_history import RequestHistoryCreate, RequestHistoryDetailRead
from services.request_history_service import RequestHistoryService


router = APIRouter(prefix="/ml-models")


@router.post("/", response_model=MLModelDetailRead)
async def create_model(
    model_data: MLModelCreate, db: Session = Depends(get_async_session)
):
    return MLModelService(db).create_model(model_data)


@router.get("/{model_id}", response_model=MLModelDetailRead)
async def get_model(model_id: int, db: Session = Depends(get_async_session)):
    model = MLModelService(db).get_model_by_id(model_id, include_details=True)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.get("/by-input/{input_type}", response_model=List[MLModelDetailRead])
async def get_models_by_input_type(
    input_type: str, limit: int = 100, db: Session = Depends(get_async_session)
):
    return MLModelService(db).get_models_by_input_type(
        input_type=input_type, include_details=True, limit=limit
    )


router = APIRouter(prefix="/model-settings")


@router.post("/", response_model=MLModelSettingDetailRead)
async def create_setting(
    setting_data: MLModelSettingCreate, db: Session = Depends(get_async_session)
):
    try:
        return MLModelSettingsService(db).create_setting(setting_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/model/{model_id}", response_model=List[MLModelSettingDetailRead])
async def get_model_settings(
    model_id: int, limit: int = 100, db: Session = Depends(get_async_session)
):
    return MLModelSettingsService(db).get_model_settings(
        model_id=model_id, include_model=True, limit=limit
    )


@router.put("/bulk-update/{model_id}")
async def bulk_update_settings(
    model_id: int,
    settings_updates: Dict[str, str],
    db: Session = Depends(get_async_session),
):
    return MLModelSettingsService(db).bulk_update_settings(
        model_id=model_id, settings_updates=settings_updates
    )


router = APIRouter(prefix="/requests")


@router.post("/", response_model=RequestHistoryDetailRead)
async def create_request(
    request_data: RequestHistoryCreate, db: Session = Depends(get_async_session)
):
    try:
        return RequestHistoryService(db).create_request(request_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/complete", response_model=RequestHistoryDetailRead)
async def complete_request(
    request_id: int,
    output_data: str,
    metrics: Optional[str] = None,
    db: Session = Depends(get_async_session),
):
    result = RequestHistoryService(db).complete_request(
        request_id=request_id, output_data=output_data, metrics=metrics
    )
    if not result:
        raise HTTPException(status_code=404, detail="Request not found")
    return result


@router.get("/user/{user_id}/stats")
async def get_user_stats(user_id: int, db: Session = Depends(get_async_session)):
    return RequestHistoryService(db).get_user_stats(user_id)
