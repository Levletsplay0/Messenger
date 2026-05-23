from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models import User, Base, Group, Message
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from sqlalchemy.orm import selectinload
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://myuser:mypass@localhost:5432/mydb")

async_engine = create_async_engine(DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with async_engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_user(username, password, email, db: AsyncSession):
    existing = await get_user_by_name(username, db)
    if existing:
        return None, 409, f"Пользователь '{username}' уже существует"
    
    hashed_password = generate_password_hash(password)
    user = User(username=username, password=hashed_password, email=email)
    db.add(user)
    await db.commit()
    return user, 200, "Пользователь успешно создан"


async def auth_user(username, password, db: AsyncSession):
    user = await get_user_by_name(username, db)
    if not user:
        return None, 404, "Такого пользователя нет"
    
    
    is_valid = await password_check(user, password)
    if not is_valid:
        return None, 401, "Неверный пароль"
    
    token = await update_auth_token(user, db)
    return token, 200, "Успешный вход"


async def get_user_by_name(username, db: AsyncSession):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()
    
async def password_check(user: User, password):
    if not user:
        return False
    return check_password_hash(user.password, password)
    
async def update_auth_token(user: User, db: AsyncSession):
    token = secrets.token_hex(32)
    user.token = token
    await db.commit()
    return token

async def get_user_by_token(token, db: AsyncSession):
    result = await db.execute(select(User).where(User.token == token))
    user = result.scalar_one_or_none()
    if user:
        return user, 200, "Пользователь найден"
    else:
        return None, 401, "Токен устарел или невалиден"


