from fastapi import (APIRouter, Depends, Header, UploadFile, File, Query, Body, Path)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.user import (get_yourself, users_search, upload_user_avatar,
                           remove_user_avatar, update_user_description, get_user_profile)

router = APIRouter(prefix="/users")

@router.get("/me")
async def get_user(auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    data, status_code, message = await get_yourself(auth_token, db)
    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data
        }
    )

@router.get("/search")
async def search_users(auth_token: str = Header(..., description="Токен аутентификации"), username: str = Query(None, description="Поиск по имени"), limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0), db: AsyncSession = Depends(get_db)):
    users, status_code, message = await users_search(auth_token, username, limit, offset, db)
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
            "data": users,
        }
    )

@router.post("/me/avatar")
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
            "data": result
        }
    )

@router.delete("/me/avatar")
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
            "data": result
        }
    )

@router.patch("/me/description")
async def update_description_user(auth_token: str = Header(..., description="Токен аутентификации"), description: str = Body(..., description="Описание пользователя", embed=True), db: AsyncSession = Depends(get_db)):
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
            "data": result
        }
    )

@router.get("/{user_id}")
async def get_user_details(user_id: int = Path(..., ge=1, description="id пользователя"), auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await get_user_profile(auth_token, user_id, db)
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