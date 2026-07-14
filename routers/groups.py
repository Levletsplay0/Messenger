from fastapi import (APIRouter, Depends, Header, UploadFile, File, Query, Body, Path, Form)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from ws_manager import manager
from services.group import (create_group, add_participants_to_group,
                            upload_group_avatar, remove_group_avatar, update_description_group,
                            group_rename, get_group, get_group_members_from_db,
                            leave_from_group, kick_users_from_group, delete_group)
from services.message import (send_message, get_group_messages, edit_message,
                              delete_message)
from services.user import get_user_groups

router = APIRouter(prefix="/groups")

@router.post("/")
async def new_group(auth_token: str = Header(..., description="Токен аутентификации"), name: str = Body(..., embed=True, description="Название группы"), db: AsyncSession = Depends(get_db)):
    new_group, status_code, message = await create_group(auth_token, name, db)
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": new_group,
        }
    )

@router.post("/{group_id}/members")
async def add_group_members(group_id: int = Path(..., ge=1, description="ID группы"), auth_token: str = Header(..., description="Токен аутентификации"), user_ids: list[int] = Body(..., embed=True, min_length=1, max_length=50, description="Список ID пользователей"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await add_participants_to_group(
        group_id=group_id,
        user_ids=user_ids,
        token=auth_token,
        db=db
    )
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
        
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.post("/{group_id}/messages")
async def send_message_to_group(group_id: int = Path(..., ge=1, description="ID группы"), auth_token: str = Header(..., description="Токен аутентификации"), content: str = Form(None, description="Текст сообщения"), file: UploadFile = File(None, description="Прикрепленный файл"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await send_message(
        token=auth_token,
        content=content,
        group_id=group_id,
        file=file,
        db=db
    )
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )

    await manager.broadcast({
        "type": "new_message",
        "data": result
    }, group_id)
        
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.get("/{group_id}/messages")
async def get_messages_group(group_id: int = Path(..., ge=1, description="ID группы"), auth_token: str = Header(..., description="Токен аутентификации"), limit: int = Query(default=20, ge=1, le=100, description="Кол-во сообщений"), offset: int = Query(default=0, ge=0, description="Смещение"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await get_group_messages(
        token=auth_token,
        group_id=group_id,
        limit=limit,
        offset=offset,
        db=db
    )
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
        
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )


@router.get("/")
async def get_groups(auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await get_user_groups(token=auth_token, db=db)
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
        
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.post("/{group_id}/avatar")
async def set_group_avatar(auth_token: str = Header(..., description="Токен аутентификации"), group_id: int = Path(..., description="id группы"), file: UploadFile = File(..., description="Файл аватарки (png, jpg, jpeg, webp)"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await upload_group_avatar(auth_token, group_id, file, db)
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.delete("/{group_id}/avatar")
async def delete_group_avatar(auth_token: str = Header(..., description="Токен аутентификации"), group_id: int = Path(..., description="id группы"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await remove_group_avatar(auth_token, group_id, db)
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.patch("/{group_id}/description")
async def update_group_description(auth_token: str = Header(..., description="Токен аутентификации"), group_id: int = Path(..., description="id группы"), description: str = Body(..., description="Описание группы", embed=True), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await update_description_group(auth_token, group_id, description, db)
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.patch("/{group_id}/name")
async def update_group_name(auth_token: str = Header(..., description="Токен аутентификации"), group_id: int = Path(..., description="id группы"), name: str = Body(..., description="Название группы", embed=True), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await group_rename(auth_token, group_id, name, db)
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.patch("/{group_id}/messages/{message_id}")
async def edit_message_endpoint(group_id: int = Path(..., ge=1, description="id группы"), message_id: int = Path(..., ge=1, description="id сообщения"), auth_token: str = Header(..., description="Токен аутентификации"), content: str = Body(..., embed=True, description="Контент сообщения"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await edit_message(auth_token, message_id, content, db)
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    await manager.broadcast({
        "type": "edit_message",
        "data": result
    }, group_id)

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.delete("/{group_id}/messages/{message_id}")
async def delete_message_endpoint(group_id: int = Path(..., ge=1, description="id группы"), message_id: int = Path(..., ge=1, description="id сообщения"), auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await delete_message(auth_token, message_id, db)
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    await manager.broadcast({
        "type": "delete_message",
        "data": result
    }, group_id)

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.get("/{group_id}")
async def get_group_details(group_id: int = Path(..., ge=1, description="id группы"), auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await get_group(auth_token, group_id, db)
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.get("/{group_id}/members")
async def get_group_members(group_id: int = Path(..., ge=1, description="id группы"), auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await get_group_members_from_db(auth_token, group_id, db)
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.post("/{group_id}/leave")
async def leave_user_from_group(group_id: int = Path(..., ge=1), auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await leave_from_group(auth_token, group_id, db)
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.post("/{group_id}/kick")
async def kick_users(group_id: int = Path(..., ge=1), user_ids: list[int] = Body(..., embed=True, min_length=1, description="Список ID пользователей"), auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await kick_users_from_group(group_id, user_ids, auth_token, db)
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@router.delete("/{group_id}/")
async def delete_group_endpoint(group_id: int = Path(..., ge=1), auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await delete_group(auth_token, group_id, db)
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )
