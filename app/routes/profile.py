# Добавим в router.py (или создадим новый файл для профиля)

from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.responses import HTMLResponse
from services.dependencies import (
    get_templates,
    get_user_service,
    get_transaction_service,
    get_request_history_service,
)
from services.user_service import UserService
from typing import List, Dict
from datetime import datetime

router = APIRouter(tags=["Profile"])


@router.get("/profile", response_class=HTMLResponse)
async def show_profile(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    templates=Depends(get_templates),
):
    try:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )

        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": user,
                "active_tab": "profile",  # Активная вкладка по умолчанию
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/profile/user-info")
async def get_user_info(
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    token = request.cookies.get("access_token")
    user = await user_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "balance": user.balance,
        # "created_at": user.created_at.isoformat() if user.created_at else None,
        # "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.get("/api/profile/ml-requests")
async def get_user_ml_requests(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    request_service=Depends(get_request_history_service),
):
    token = request.cookies.get("access_token")
    user = await user_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    ml_requests = await request_service.get_user_requests(
        user_id=user.id,
        limit=100,  # или любое другое значение
        include_details=False,  # если нужны детали
    )
    return [
        {
            "id": ml_request.id,
            "model_id": ml_request.model_id,
            "created_at": (
                ml_request.created_at.isoformat() if ml_request.created_at else None
            ),
            "input": ml_request.input_data,
            "response": ml_request.output_data,
            # "status": ml_request.status,
            # Добавьте другие datetime поля при необходимости
        }
        for ml_request in ml_requests
    ]


@router.get("/api/profile/transactions")
async def get_user_transactions(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    transaction_service=Depends(get_transaction_service),
):
    token = request.cookies.get("access_token")
    user = await user_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    transactions = await transaction_service.get_user_transactions(
        user_id=user.id,
        limit=100,  # или любое другое значение
        include_details=False,  # если нужны детали
    )
    return [
        {
            **transaction.dict(),
            "created_at": (
                transaction.created_at.isoformat() if transaction.created_at else None
            ),
            # Добавьте другие datetime поля при необходимости
        }
        for transaction in transactions
    ]
