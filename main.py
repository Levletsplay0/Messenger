from fastapi import FastAPI, Depends, Header, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import (UserRegister, UserLogin, TaskCreate, TaskStatusUpdate)
from database import (init_db, get_db, create_user, get_user_by_token, auth_user,
                      user_logout)

from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/")
async def main():
    return {"success": True, "message": "This is a future project with task management for users."}

@app.post("/register")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result, status_code, message = await create_user(data.username, data.password, data.email, db)
    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    return {"success": True, "message": message, "data": {"id": result.id, "username": result.username}}

@app.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result, status_code, message = await auth_user(data.username, data.password, db)
    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    return {"success": True, "message": message, "data": {"access_token": result}}

    
@app.get("/users/me")
async def get_user(auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    user, status_code, message = await get_user_by_token(auth_token, db)
    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    return {
        "success": True,
        "message": message,
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

@app.post("/logout")
async def logout(auth_token: str = Header(..., description="Токен аутентификации"), db: AsyncSession = Depends(get_db)):
    user, status_code, message = await user_logout(auth_token, db)
    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": message}
        )
    
    return {
        "success": True,
        "message": message,
    }





