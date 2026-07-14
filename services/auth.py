from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Base, Group, Message, GroupMember
from werkzeug.security import generate_password_hash, check_password_hash
from services.user import (get_user_by_name, get_user_by_email, get_user_by_token)
import secrets


async def create_user(username, password, email, name, last_name, db: AsyncSession):
    existing_username = await get_user_by_name(username, db)
    if existing_username:
        return None, 409, f"Пользователь с никнеймом: {username} уже существует"
    
    existing_email = await get_user_by_email(email, db)
    if existing_email:
        return None, 409, f"Пользователь с почтой: {email} уже существует"
    
    hashed_password = generate_password_hash(password)
    user = User(username=username, password=hashed_password, name=name, last_name=last_name, email=email)
    db.add(user)
    await db.commit()
    
    await db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "last_name": user.last_name
    }, 201, "Пользователь успешно создан"


async def auth_user(username, password, db: AsyncSession):
    user = await get_user_by_name(username, db)
    if not user:
        return None, 404, "Такого пользователя нет"
    
    
    is_valid = await check_password_hash(user.password, password)
    if not is_valid:
        return None, 401, "Неверный пароль"
    
    token = await update_auth_token(user, db)
    return token, 200, "Успешный вход"


async def update_auth_token(user: User, db: AsyncSession):
    token = secrets.token_hex(32)
    user.token = token
    await db.commit()
    return token


async def user_logout(token, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message
    
    user.token = None
    await db.commit()
    return {"is_logged_out": True}, 200, "Вы разлогинены"