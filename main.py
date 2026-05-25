from fastapi import FastAPI, Depends, Header, Path, Body, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import (UserRegister, UserLogin)
from database import (init_db, get_db, create_user, get_user_by_token, auth_user,
                      user_logout, users_search, create_group, add_participants_to_group,
                      send_message, get_group_messages)

from contextlib import asynccontextmanager



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
                "email": user.email
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