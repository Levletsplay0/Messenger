from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Group, GroupMember, Message
from pathlib import Path
from fastapi import UploadFile
import uuid
from constants import (ALLOWED_EXTENSIONS, MAX_FILE_SIZE, 
                       USER_AVATARS_DIR)


async def get_user_by_name(username, db: AsyncSession):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_email(email, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_token(token, db: AsyncSession):
    result = await db.execute(select(User).where(User.token == token))
    user = result.scalar_one_or_none()
    if not user:
        return None, 401, "Токен устарел или невалиден"
    
    return user, 200, "Пользователь найден"

async def get_yourself(token, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message

    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "last_name": user.last_name,
        "avatar_path": user.avatar_path,
        "description": user.description,
    }
    
    return data, 200, "Пользователь найден"


async def users_search(token, username, limit, offset, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message
    
    if not username:
        return [], 400, "Имя не может быть пустым"
    
    result = await db.execute(select(User).where(User.username.ilike(f"%{username}%")).limit(limit).offset(offset))
    users = result.scalars().all()
    if not users:
        return [], 200, "Пользователи не найдены"
    
    users_data = [
        {"id": u.id, "username": u.username, "email": u.email, "name": u.name, "last_name": u.last_name, "avatar_path": u.avatar_path, "description": u.description}
        for u in users
    ]
    
    return users_data, 200, f"Найдено {len(users_data)} пользователей"

async def get_user_groups(token, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message

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

    group_ids = [group.id for group, role in rows]
    last_messages_map = {}
    
    if group_ids:
        latest_msgs_stmt = (
            select(Message, User.username, User.avatar_path)
            .join(User, Message.author_id == User.id)
            .where(Message.group_id.in_(group_ids))
            .distinct(Message.group_id)
            .order_by(Message.group_id, desc(Message.sent_at))
        )
        msgs_result = await db.execute(latest_msgs_stmt)
        
        for msg, author_username, author_avatar in msgs_result.all():
            last_messages_map[msg.group_id] = {
                "id": msg.id,
                "content": msg.content,
                "author_id": msg.author_id,
                "author_username": author_username,
                "author_avatar_path": author_avatar,
                "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
                "edited_at": msg.edited_at.isoformat() if msg.edited_at else None,
                "file_name": msg.file_name,
                "file_path": msg.file_path
            }

    data = []
    for group, role in rows:
        group_data = {
            "id": group.id,
            "name": group.name,
            "avatar_path": group.avatar_path,
            "description": group.description,
            "creator_id": group.creator_id,
            "my_role": role,
            "last_message": last_messages_map.get(group.id)
        }
        data.append(group_data)

    return data, 200, f"Загружено {len(data)} чатов"

async def upload_user_avatar(token: str, file: UploadFile, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message
    
    if user.avatar_path:
        path = Path(user.avatar_path)
        if path.exists() and path.is_file():
            path.unlink()

    if not file.filename:
        return None, 400, "Файл не указан"
    
    if Path(file.filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        return None, 400, f"Разрешены только: {', '.join(ALLOWED_EXTENSIONS)}"
    
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        return None, 413, f"Размер файла не должен превышать {MAX_FILE_SIZE // 1024 // 1024} МБ"


    ext = Path(file.filename).suffix.lower()
    unique_filename = f"{user.id}_{uuid.uuid4().hex}{ext}"

    USER_AVATARS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = USER_AVATARS_DIR / unique_filename

    with open(file_path, "wb") as f:
        f.write(contents)

    user.avatar_path = str(file_path)
    await db.commit()

    return {"avatar_path": str(file_path)}, 200, "Аватарка успешно обновлена"


async def remove_user_avatar(token: str, db: AsyncSession):    
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message

    if user.avatar_path:
        path = Path(user.avatar_path)
        if path.exists() and path.is_file():
            path.unlink()
    
    user.avatar_path = None
    await db.commit()

    return {"is_deleted": True}, 200, "Аватарка успешно удалена"

async def update_user_description(token: str, description: str, db: AsyncSession):    
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message

    if not description or not description.strip():
        return None, 400, "Описание не может быть пустым"
    
    if len(description) > 100:
        return None, 400, "Описание слишком длинное (макс. 100 символов)"

    
    user.description = description.strip()
    await db.commit()

    return {"is_updated": True}, 200, "Описание обновлено!"

async def get_user_profile(token: str, user_id: int, db: AsyncSession):
    requester, status_code, message = await get_user_by_token(token, db)
    if not requester:
        return None, status_code, message

    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return None, 404, "Такого пользователя нет"

    user_data = {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "last_name": user.last_name,
        "description": user.description,
        "avatar_path": user.avatar_path,
    }


    return user_data, 200, "Пользователь найден"
