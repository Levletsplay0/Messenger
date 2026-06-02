from fastapi import FastAPI, Depends, Header, Path, Body, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import (UserRegister, UserLogin)
from database import (init_db, get_db, create_user, get_user_by_token, auth_user,
                      user_logout, users_search, create_group, add_participants_to_group,
                      send_message, get_group_messages, get_user_groups, upload_user_avatar,
                      remove_user_avatar, upload_group_avatar, remove_group_avatar,
                      update_description_group, group_rename, update_user_description)

from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/")
async def main():
    return {"success": True, "message": "Прекрасно, бекенд работает!"}

@app.post("/register")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result, status_code, message = await create_user(data.username, data.password, data.email, db)
    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    return JSONResponse (
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": {"id": result.id, "username": result.username}
        }
    )
@app.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result, status_code, message = await auth_user(data.username, data.password, db)
    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    return JSONResponse (
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": {"access_token": result}
        }
    )
    
@app.get("/users/me")
async def get_user(auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    user, status_code, message = await get_user_by_token(auth_token, db)
    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    

    return JSONResponse (
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar_path": user.avatar_path,
                "description": user.description
            }
        }
    )

@app.post("/logout")
async def logout(auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    user, status_code, message = await user_logout(auth_token, db)
    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    return JSONResponse (
        status_code=status_code,
        content={
            "success": True,
            "message": message,
        }
    )


@app.get("/users/search")
async def search_users(auth_token: str = Header(..., description="Токен аутентификации"), username: str = Query(None, description="Поиск по имени"), limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0), db: AsyncSession = Depends(get_db)):
    users, status_code, message = await users_search(auth_token, username, limit, offset, db)
    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    

    return JSONResponse (
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": users,
        }
    )

@app.post("/groups")
async def new_group(auth_token: str = Header(..., description="Токен аутентификации"), name: str = Body(..., embed=True, description="Название группы"), db: AsyncSession = Depends(get_db)):
    new_group, status_code, message = await create_group(auth_token, name, db)
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    return JSONResponse (
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": new_group,
        }
    )


@app.post("/groups/{group_id}/members")
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
        
    return JSONResponse (
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )


@app.post("/groups/{group_id}/messages")
async def send_message_to_group(group_id: int = Path(..., ge=1, description="ID группы"), auth_token: str = Header(..., description="Токен аутентификации"), content: str = Body(..., embed=True, description="Контент сообщения"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await send_message(
        token=auth_token,
        content=content,
        group_id=group_id,
        db=db
    )
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
        
    return JSONResponse (
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@app.get("/groups/{group_id}/messages")
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
        
    return JSONResponse (
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@app.get("/groups")
async def get_groups(auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await get_user_groups(token=auth_token, db=db)
    
    if status_code != 200 and status_code != 201:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
        
    return JSONResponse (
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": result
        }
    )

@app.post("/users/me/avatar")
async def set_user_avatar(auth_token: str = Header(..., description="Токен аутентификации"), file: UploadFile = File(..., description="Файл аватарки (png, jpg, jpeg, webp)"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await upload_user_avatar(auth_token, file, db)
    
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
            "data": {"avatar_path": result}
        }
    )

@app.delete("/users/me/avatar")
async def delete_user_avatar(auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await remove_user_avatar(auth_token, db)
    
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
            "data": {"is_deleted": result}
        }
    )

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/groups/{group_id}/avatar")
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
            "data": {"avatar_path": result}
        }
    )

@app.delete("/groups/{group_id}/avatar")
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
            "data": {"is_deleted": result}
        }
    )


@app.patch("/groups/{group_id}/description")
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
            "data": {"is_updated": result}
        }
    )

@app.patch("/groups/{group_id}/name")
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
            "data": {"is_updated": result}
        }
    )


@app.patch("/users/me/description")
async def update_description_user(auth_token: str = Header(..., description="Токен аутентификации"), description: str = Body(..., description="Описание группы", embed=True), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await update_user_description(auth_token, description, db)
    
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
            "data": {"is_updated": result}
        }
    )