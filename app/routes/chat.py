from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from auth.jwt_handler import verify_access_token
from services.dependencies import get_current_user
from services.dependencies import get_templates

router = APIRouter(tags=["WebSocket Chat"])
active_connections = []  # Пока тут, потом — в Redis (как джинн в бутылке)


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket, token: str = Query(...)):
    if not verify_access_token(token):  # Твоя функция проверки
        await websocket.close(code=1008)  # Закрываем соединение
        return
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            user_message = await websocket.receive_text()
            bot_response = (
                f"Йети: {user_message.upper()}... " f"А ВОТ И НЕТ! *роняет сервер* 😈"
            )
            await websocket.send_text(bot_response)

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("Клиент испарился, как переменная вне скоупа.")


@router.get("/chat", name="chat")
async def private_chat(
    request: Request,
    user: str = Depends(get_current_user),
    templates=Depends(get_templates),
):
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})
