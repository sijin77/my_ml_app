from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer
from services.dependencies import (
    get_ml_orchestrator_service,
    get_templates,
    get_user_service,
)
from services.ml_queue_request_service import MLRequestOrchestratorService
from services.user_service import UserService
from pydantic import BaseModel
from typing import Dict, List

router = APIRouter(tags=["Chat"])
security = HTTPBearer()

# Храним историю чата в памяти (ключ - user_id)
chat_history: Dict[int, List[Dict[str, str]]] = {}


class ChatMessage(BaseModel):
    user_id: int
    text: str


@router.get("/chat")
async def show_chat(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    templates=Depends(get_templates),
):
    try:
        token = request.cookies.get("access_token")
        if not token:
            # Перенаправляем на страницу входа, если нет токена
            return templates.TemplateResponse(
                "login.html", {"request": request, "error": "Требуется авторизация"}
            )

        user = await user_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return templates.TemplateResponse(
            "chat.html",
            {
                "request": request,
                "user": user,  # Передаем весь объект пользователя
                "history": chat_history.get(user.id, []),
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


@router.post("/send-message")
async def send_message(
    message: ChatMessage,
    request: Request,
    orchestrator: MLRequestOrchestratorService = Depends(get_ml_orchestrator_service),
    user_service: UserService = Depends(get_user_service),
):
    try:
        token = request.cookies.get("access_token")
        user = await user_service.get_current_user(token)

        if message.user_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

        # Инициализируем историю чата для пользователя, если ее еще нет
        if message.user_id not in chat_history:
            chat_history[message.user_id] = []

        # Добавляем сообщение пользователя
        chat_history[message.user_id].append(
            {
                "sender": "user",
                "text": message.text,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Получаем ответ от ML модели
        response = await orchestrator.process_prediction_request(
            user_id=message.user_id,
            model_id=1,
            input_data=message.text,
            request_type="prediction",
        )

        # Добавляем ответ модели
        chat_history[message.user_id].append(
            {
                "sender": "model",
                "text": response.output_data,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return {"status": "success", "answer": response.output_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
