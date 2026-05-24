from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models import User, Base, Group, Message, GroupMember
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
    async with async_engine.begin() as conn:
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


async def user_logout(token, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token=token, db=db)
    if user:
        user.token = None
        await db.commit()
        return user, 200, "Вы разлогинены"
    else:
        return None, 401, "Токен устарел или невалиден"


async def users_search(token, username, limit, offset, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token=token, db=db)
    if user:
        stmt = select(User)
        if username:
            stmt = stmt.where(User.username.ilike(f"%{username}%"))
        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        users = result.scalars().all()
        if not users:
            return [], 200, "Пользователи не найдены"
        
        users_data = [
            {"id": u.id, "username": u.username, "email": u.email}
            for u in users
        ]
        
        return users_data, 200, f"Найдено {len(users_data)} пользователей"

    else:
        return None, 401, "Токен устарел или невалиден"


async def create_group(token, name, db: AsyncSession):
    creator, status_code, message = await get_user_by_token(token=token, db=db)
    if not creator:
        return None, status_code, message
    
    new_group = Group(
        name=name,
        creator_id=creator.id
    )

    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    
    return {
        "id": new_group.id,
        "name": new_group.name,
        "creator_id": new_group.creator_id,
    }, 201, "Группа успешно создана"


async def add_participants_to_group(token, group_id, user_ids, db: AsyncSession):
    requester, status_code, message = await get_user_by_token(token=token, db=db)
    if not requester:
        return None, status_code, message
    
    stmt = select(Group).where(Group.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()
    if not group:
        return None, 404, "Группа не найдена"
    
    is_creator = group.creator_id == requester.id

    if not is_creator:
        admin_stmt = select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == requester.id,
            GroupMember.role == "admin"
        )
        admin_res = await db.execute(admin_stmt)
        if not admin_res.scalar_one_or_none():
            return None, 403, "Только создатель или админ может добавлять участников"
    
    if not user_ids:
        return None, 400, "Список участников пуст"
    
    existing_stmt = select(GroupMember.user_id).where(GroupMember.group_id == group_id)
    existing_res = await db.execute(existing_stmt)
    existing_ids = set(existing_res.scalars().all())

    new_ids = [uid for uid in user_ids if uid not in existing_ids]
    if not new_ids:
        return None, 409, "Все указанные пользователи уже в группе"
    
    users_stmt = select(User.id).where(User.id.in_(new_ids))
    users_res = await db.execute(users_stmt)
    found_ids = set(users_res.scalars().all())
    missing = set(new_ids) - found_ids
    
    if missing:
        return None, 404, f"Пользователи с ID {list(missing)} не найдены"

    
    db.add_all([
        GroupMember(group_id=group_id, user_id=uid, role="member")
        for uid in new_ids
    ])
    await db.commit()

    return {
        "group_id": group_id,
        "added_count": len(new_ids),
        "added_user_ids": new_ids
    }, 201, f"Добавлено {len(new_ids)} участников"