from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from schemas import UserRegister, UserLogin
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.auth import create_user, auth_user, user_logout

router = APIRouter()

@router.post("/register")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result, status_code, message = await create_user(data.username, data.password, data.email, data.name, data.last_name, db)
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

@router.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result, status_code, message = await auth_user(data.username, data.password, db)
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
            "data": {"auth_token": result}
        }
    )


@router.post("/logout")
async def logout(auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    result, status_code, message = await user_logout(auth_token, db)
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