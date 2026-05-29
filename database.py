from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models import User, Base, Group, Message, GroupMember
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from sqlalchemy.orm import selectinload
import os
from pathlib import Path
from fastapi import UploadFile
import uuid

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
    existing_username = await get_user_by_name(username, db)
    if existing_username:
        return None, 409, f"Пользователь с никнеймом: {username} уже существует"
    
    existing_email = await get_user_by_email(email, db)
    if existing_email:
        return None, 409, f"Пользователь с почтой: {email} уже существует"
    
    hashed_password = generate_password_hash(password)
    user = User(username=username, password=hashed_password, email=email)
    db.add(user)
    await db.commit()
    return user, 201, "Пользователь успешно создан"


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
    
async def get_user_by_email(email, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == email))
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
        return None, status_code, message


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
        return None, status_code, message


async def create_group(token, name, db: AsyncSession):
    creator, status_code, message = await get_user_by_token(token=token, db=db)
    if not creator:
        return None, status_code, message
    
    new_group = Group(
        name=name,
        creator_id=creator.id
    )

    db.add(new_group)

    await db.flush()

    creator_member = GroupMember(
        group_id=new_group.id,
        user_id=creator.id,
        role="admin"
    )
    db.add(creator_member)

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


async def send_message(token, content, group_id, db: AsyncSession):
    author, status_code, message = await get_user_by_token(token=token, db=db)
    if not author:
        return None, status_code, message
    
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        return None, 404, "Группа не найдена"
    
    member_stmt = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == author.id
    )
    member_res = await db.execute(member_stmt)
    if not member_res.scalar_one_or_none():
        return None, 403, "Только участники группы могут отправлять сообщения"
    
    if not content or not content.strip():
        return None, 400, "Сообщение не может быть пустым"
    
    if len(content) > 5000:
        return None, 400, "Сообщение слишком длинное (макс. 5000 символов)"
    
    new_message = Message(
        content=content.strip(),
        author_id=author.id,
        group_id=group_id,
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    return {
        "id": new_message.id,
        "content": new_message.content,
        "sender_id": new_message.author_id,
        "sender_username": author.username,
        "group_id": new_message.group_id,
        "sent_at": new_message.sent_at.isoformat() if new_message.sent_at else None
    }, 201, "Сообщение отправлено"


async def get_group_messages(token, group_id, limit, offset, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token=token, db=db)
    if not user:
        return [], status_code, message
    
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        return [], 404, "Группа не найдена"
    

    member_res = await db.execute(select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user.id))
    if not member_res.scalar_one_or_none():
        return [], 403, "Только участники группы могут отправлять сообщения"
    
    
    
    msg_stmt = (
        select(Message)
        .options(selectinload(Message.author))
        .where(Message.group_id == group_id)
        .order_by(Message.sent_at.asc()) #можно ещё .desc() чтобы было от новых к старым
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(msg_stmt)
    messages = result.scalars().all()

    if not messages:
        return [], 200, "Сообщений нет"

    data = [
        {
            "id": m.id,
            "content": m.content,
            "author_id": m.author_id,
            "author_username": m.author.username,
            "group_id": m.group_id,
            "sent_at": m.sent_at.isoformat() if m.sent_at else None
        }
        for m in messages
    ]

    return data, 200, f"Загружено {len(data)} сообщений"

async def get_user_groups(token, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token=token, db=db)
    if not user:
        return [], status_code, message

    stmt = (
        select(Group, GroupMember.role)
        .join(GroupMember, Group.id == GroupMember.group_id)
        .where(GroupMember.user_id == user.id)
        .order_by(GroupMember.joined_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all() 
    if not rows:
        return [], 200, "У вас пока нет групп"
    
    data = [
        {
            "id": group.id,
            "name": group.name,
            "creator_id": group.creator_id,
            "my_role": role
        }
        for group, role in rows
    ]

    return data, 200, f"Загружено {len(data)} чатов"


def _is_allowed_file(filename: str):
    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

async def upload_user_avatar(token: str, file: UploadFile, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token=token, db=db)
    if not user:
        return None, status_code, message

    if not file.filename:
        return None, 400, "Файл не указан"
    
    if not _is_allowed_file(file.filename):
        ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
        return None, 400, f"Разрешены только: {', '.join(ALLOWED_EXTENSIONS)}"
    
    MAX_FILE_SIZE = 5 * 1024 * 1024
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        return None, 413, f"Размер файла не должен превышать {MAX_FILE_SIZE // 1024 // 1024} МБ"


    ext = Path(file.filename).suffix.lower()
    unique_filename = f"{user.id}_{uuid.uuid4().hex}{ext}"

    AVATARS_DIR = Path("static/avatars")
    AVATARS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = AVATARS_DIR / unique_filename

    with open(file_path, "wb") as f:
        f.write(contents)

    user.avatar_path = str(file_path)
    await db.commit()

    return str(file_path), 200, "Аватарка успешно обновлена"


async def remove_user_avatar(token: str, db: AsyncSession):    
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message

    if user.avatar_path and os.path.exists(user.avatar_path):
        os.remove(user.avatar_path)
    
    user.avatar_path = None
    await db.commit()

    return True, 200, "Аватарка успешно удалена"