from fastapi import (APIRouter, WebSocket, WebSocketDisconnect)
from database import AsyncSessionLocal
from ws_manager import manager
import json
from services.message import (edit_message, delete_message, send_message)
from services.ws import check_permissions_ws

router = APIRouter()


@router.websocket("/ws/{group_id}")
async def websocket_endpoint(websocket: WebSocket, group_id: int, token: str):

    async with AsyncSessionLocal() as db:
        user, status_code, message = await check_permissions_ws(token, group_id, db)
        if status_code != 200 and status_code != 201:
            await websocket.close(code=status_code, reason=message)
            return

    await manager.connect(websocket, group_id)

    try:
        while True:
            raw = await websocket.receive_text()
            if not raw or not raw.strip():
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Ожидается JSON"})
                continue

            action = data.get("action", "send_message")
            async with AsyncSessionLocal() as db:
                if action == "send_message":
                    content = data.get("content", "").strip()
                    if not content:
                        await websocket.send_json({"error": "Пустое сообщение"})
                        continue
                    if len(content) > 5000:
                        await websocket.send_json({"error": "Слишком длинное сообщение"})
                        continue

                    result, status_code, message = await send_message(token, content, group_id, db)
                    if status_code != 200 and status_code != 201:
                        await websocket.send_json({"error": message})
                        continue

                    await manager.broadcast({
                        "type": "new_message",
                        "data": result
                    }, group_id)

                elif action == "edit_message":
                    message_id = data.get("message_id")
                    new_content = data.get("content", "").strip()
                    if not message_id:
                        await websocket.send_json({"error": "Не указан message_id"})
                        continue

                    result, status_code, message = await edit_message(token, message_id, new_content, db)
                    if status_code != 200 and status_code != 201:
                        await websocket.send_json({"error": message})
                        continue

                    await manager.broadcast({
                        "type": "edit_message",
                        "data": result
                    }, group_id)

                elif action == "delete_message":
                    message_id = data.get("message_id")
                    if not message_id:
                        await websocket.send_json({"error": "Не указан message_id"})
                        continue

                    result, status_code, message = await delete_message(token, message_id, db)
                    if status_code != 200 and status_code != 201:
                        await websocket.send_json({"error": message})
                        continue

                    await manager.broadcast({
                        "type": "delete_message",
                        "data": result
                    }, group_id)

                elif action == "typing":
                    await manager.broadcast({
                        "type": "typing",
                        "data": {
                            "user_id": user.id,
                            "username": user.username
                        }
                    }, group_id, exclude_websocket=websocket)
                
                elif action == "stop_typing":
                    await manager.broadcast({
                        "type": "stop_typing",
                        "data": {
                            "user_id": user.id,
                            "username": user.username
                        }
                    }, group_id, exclude_websocket=websocket)

                else:
                    await websocket.send_json({"error": f"Неизвестное действие: {action}"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, group_id)
    except Exception as e:
        manager.disconnect(websocket, group_id)