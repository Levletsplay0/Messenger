from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import Group, Message, GroupMember
from sqlalchemy.orm import selectinload
from pathlib import Path
from fastapi import UploadFile
import uuid
from constants import MESSAGE_FILES_DIR
from datetime import datetime, timezone
from services.user import get_user_by_token



async def send_message(token, content, group_id, db: AsyncSession, file: UploadFile = None):
    author, status_code, message = await get_user_by_token(token, db)
    if not author:
        return None, status_code, message
    
    has_content = content and content.strip()
    has_file = file and file.filename

    if not has_content and not has_file:
        return None, 400, "Сообщение не может быть пустым"

    if has_content and len(content) > 5000:
        return None, 400, "Сообщение слишком длинное (макс. 5000 символов)"
    
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
    
    file_path = None
    file_name = None
    file_size = None

    if has_file:
        contents = await file.read()

        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"

        MESSAGE_FILES_DIR.mkdir(parents=True, exist_ok=True)
        file_full_path = MESSAGE_FILES_DIR / unique_filename

        with open(file_full_path, "wb") as f:
            f.write(contents)
        
        file_path = str(file_full_path)
        file_name = file.filename
        file_size = len(contents)

    new_message = Message(
        content=content.strip() if has_content else None,
        author_id=author.id,
        group_id=group_id,
        file_path=file_path,
        file_name=file_name,
        file_size=file_size
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    return {
        "id": new_message.id,
        "content": new_message.content,
        "author_id": new_message.author_id,
        "author_username": author.username,
        "author_avatar_path": author.avatar_path,
        "group_id": new_message.group_id,
        "sent_at": new_message.sent_at.isoformat() if new_message.sent_at else None,
        "file": {
            "path": new_message.file_path,
            "name": new_message.file_name,
            "size": new_message.file_size
        } if new_message.file_path else None
    }, 201, "Сообщение отправлено"


async def get_group_messages(token, group_id, limit, offset, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message
    
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        return [], 404, "Группа не найдена"
    

    member_res = await db.execute(select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user.id))
    if not member_res.scalar_one_or_none():
        return [], 403, "Только участники группы могут просматривать сообщения"
    
    
    msg_stmt = (
        select(Message)
        .options(selectinload(Message.author))
        .where(Message.group_id == group_id)
        .order_by(Message.sent_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(msg_stmt)
    messages = result.scalars().all()

    if not messages:
        return [], 200, "Сообщений нет"
    
    messages = list(reversed(messages)) 

    data = [
        {
            "id": m.id,
            "content": m.content,
            "author_id": m.author_id,
            "author_username": m.author.username,
            "author_avatar_path": m.author.avatar_path,
            "group_id": m.group_id,
            "sent_at": m.sent_at.isoformat() if m.sent_at else None,
            "edited_at": m.edited_at.isoformat() if m.edited_at else None,
            "file": {
                "path": m.file_path,
                "name": m.file_name,
                "size": m.file_size
            } if m.file_path else None
        }
        for m in messages
    ]

    return data, 200, f"Загружено {len(data)} сообщений"

async def edit_message(token: str, message_id: int, new_content: str, db: AsyncSession):
    author, status_code, message = await get_user_by_token(token, db)
    if not author:
        return None, status_code, message

    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        return None, 404, "Сообщение не найдено"

    if msg.author_id != author.id:
        return None, 403, "Только автор может редактировать сообщение"

    if not new_content or not new_content.strip():
        return None, 400, "Сообщение не может быть пустым"

    if len(new_content) > 5000:
        return None, 400, "Сообщение слишком длинное (макс. 5000 символов)"

    msg.content = new_content.strip()
    msg.edited_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(msg)

    return {
        "id": msg.id,
        "content": msg.content,
        "author_id": msg.author_id,
        "author_username": author.username,
        "author_avatar_path": author.avatar_path,
        "group_id": msg.group_id,
        "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
        "edited_at": msg.edited_at.isoformat() if msg.edited_at else None,
        "file": {
            "path": msg.file_path,
            "name": msg.file_name,
            "size": msg.file_size
        } if msg.file_path else None
    }, 200, "Сообщение отредактировано"


async def delete_message(token: str, message_id: int, db: AsyncSession):
    author, status_code, message = await get_user_by_token(token, db)
    if not author:
        return None, status_code, message

    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        return None, 404, "Сообщение не найдено"


    if msg.author_id != author.id:
        return None, 403, "Только автор может удалять сообщение"
    
    deleted_message_data = {
        "id": msg.id,
        "group_id": msg.group_id,
    }
    
    if msg.file_path:
        path = Path(msg.file_path)
        if path.exists() and path.is_file():
            path.unlink()

    await db.delete(msg)
    await db.commit()

    return deleted_message_data, 200, "Сообщение удалено"

