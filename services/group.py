from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Base, Group, Message, GroupMember
from pathlib import Path
from fastapi import UploadFile
import uuid
from constants import (ALLOWED_EXTENSIONS, MAX_FILE_SIZE, 
                       GROUP_AVATARS_DIR)

from services.user import get_user_by_token

async def create_group(token, name, db: AsyncSession):
    creator, status_code, message = await get_user_by_token(token, db)
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
        "created_at": new_group.created_at.isoformat(),
    }, 201, "Группа успешно создана"



async def add_participants_to_group(token, group_id, user_ids, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message
    
    if not user_ids:
        return None, 400, "Список участников пуст"
    
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        return None, 404, "Группа не найдена"
    
    is_creator = group.creator_id == user.id

    if not is_creator:
        admin_res = await db.execute(select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user.id,
            GroupMember.role == "admin"
        ))
        if not admin_res.scalar_one_or_none():
            return None, 403, "Только создатель или админ может добавлять участников"
    
    
    existing_res = await db.execute(select(GroupMember.user_id).where(GroupMember.group_id == group_id))
    existing_ids = set(existing_res.scalars().all())

    new_ids = [uid for uid in user_ids if uid not in existing_ids]
    if not new_ids:
        return None, 409, "Все указанные пользователи уже в группе"
    
    users_res = await db.execute(select(User.id).where(User.id.in_(new_ids)))
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


async def upload_group_avatar(token: str, group_id: int, file: UploadFile, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message
    
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        return None, 404, "Такой группы не существует"
    
    member_res = await db.execute(select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user.id))
    if not member_res.scalar_one_or_none():
        return None, 403, "Только участники группы могут добавлять аватар"
    
    if group.avatar_path:
        path = Path(group.avatar_path)
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
    unique_filename = f"{group_id}_{uuid.uuid4().hex}{ext}"

    GROUP_AVATARS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = GROUP_AVATARS_DIR / unique_filename

    with open(file_path, "wb") as f:
        f.write(contents)

    
    group.avatar_path = str(file_path)
    await db.commit()

    return {"avatar_path": str(file_path)}, 200, "Аватарка группы успешно обновлена"

async def remove_group_avatar(token: str, group_id: int, db: AsyncSession):    
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        return None, 404, "Такой группы не существует"

    member_res = await db.execute(select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user.id))
    if not member_res.scalar_one_or_none():
        return None, 403, "Только участники группы могут добавлять аватар"
    
    if group.avatar_path:
        path = Path(group.avatar_path)
        if path.exists() and path.is_file():
            path.unlink()
    
    group.avatar_path = None
    await db.commit()

    return {"is_deleted": True}, 200, "Аватарка группы успешно удалена"

async def update_description_group(token: str, group_id: int, description: str, db: AsyncSession):    
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message

    if not description or not description.strip():
        return None, 400, "Описание не может быть пустым"
    
    if len(description) > 100:
        return None, 400, "Описание слишком длинное (макс. 100 символов)"
    
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        return None, 404, "Такой группы не существует"

    member_res = await db.execute(select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user.id))
    if not member_res.scalar_one_or_none():
        return None, 403, "Только участники группы могут изменять описание"
    
    
    group.description = description.strip()
    await db.commit()

    return {"is_updated": True}, 200, "Описание группы обновлено!"

async def group_rename(token: str, group_id: int, name: str, db: AsyncSession):    
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message

    if not name or not name.strip():
        return None, 400, "Имя не может быть пустым"
    
    if len(name) > 20:
        return None, 400, "Имя слишком длинное (макс. 20 символов)"
    
    if len(name) < 5:
        return None, 400, "Имя слишком короткое (мин. 5 символов)"
    

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        return None, 404, "Такой группы не существует"

    member_res = await db.execute(select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user.id))
    if not member_res.scalar_one_or_none():
        return None, 403, "Только участники группы могут изменять имя"
    
    
    group.name = name.strip()
    await db.commit()

    return {"is_updated": True}, 200, "Имя группы обновлено!"

async def get_group(token: str, group_id: int, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        return None, 404, "Группа не найдена"
    
    member_res = await db.execute(select(GroupMember).where(
        GroupMember.group_id == group_id, 
        GroupMember.user_id == user.id
    ))
    
    if not member_res.scalar_one_or_none():
        return None, 403, "Только участники группы могут получить данные группы"
    
    member_count_res = await db.execute(
        select(func.count(GroupMember.id)).where(GroupMember.group_id == group_id)
    )
    member_count = member_count_res.scalar()
        
    group_data = {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "avatar_path": group.avatar_path,
        "creator_id": group.creator_id,
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "member_count": member_count
    }


    return group_data, 200, "Группа найдена"


async def kick_users_from_group(group_id: int, user_ids: list[int], token: str, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message
    
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    if not group:
        return None, 404, "Группа не найдена"
    

    is_creator = group.creator_id == user.id

    if not is_creator:
        admin_res = await db.execute(select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user.id,
            GroupMember.role == "admin"
        ))
        if not admin_res.scalar_one_or_none():
            return None, 403, "Только создатель или админ может исключать участников"
    
    if user.id in user_ids:
        return None, 400, "Нельзя исключить самого себя"
    
    if group.creator_id in user_ids:
        return None, 403, "Нельзя исключить создателя группы"
    
    users_res = await db.execute(select(User.id).where(User.id.in_(user_ids)))
    found_ids = set(users_res.scalars().all())
    missing = set(user_ids) - found_ids
    if missing:
        return None, 404, f"Пользователи с ID {list(missing)} не найдены"
    

    members_res = await db.execute(
        select(GroupMember.user_id).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id.in_(user_ids)
        )
    )
    member_ids = set(members_res.scalars().all())
    not_members = set(user_ids) - member_ids
    if not_members:
        return None, 400, f"Пользователи с ID {list(not_members)} не состоят в группе"
    
    if not is_creator:
        kicked_admins_res = await db.execute(
            select(GroupMember.user_id).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id.in_(user_ids),
                GroupMember.role == "admin"
            )
        )
        kicked_admins = set(kicked_admins_res.scalars().all())
        if kicked_admins:
            return None, 403, "Админ может исключать только обычных участников"
        
    await db.execute(
        GroupMember.__table__.delete().where(
            GroupMember.group_id == group_id,
            GroupMember.user_id.in_(user_ids)
        )
    )
    await db.commit()

    data = {
        "group_id": group_id,
        "kicked_count": len(user_ids),
        "kicked_user_ids": user_ids
    }
    
    return data, 200, f"Исключено {len(user_ids)} участников"

async def get_group_members_from_db(token: str, group_id: int, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message
    
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    if not group:
        return None, 404, "Группа не найдена"
    
    member_res = await db.execute(select(GroupMember).where(
        GroupMember.group_id == group_id, 
        GroupMember.user_id == user.id
    ))
    
    if not member_res.scalar_one_or_none():
        return None, 403, "Только участники группы могут получить участников группы"
    

    stmt = (
        select(User, GroupMember.role, GroupMember.joined_at)
        .join(GroupMember, User.id == GroupMember.user_id)
        .where(GroupMember.group_id == group_id)
        .order_by(GroupMember.joined_at.asc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return [], 200, "Пока нет участников"
    
    data = [
        {
            "id": u.id,
            "username": u.username,
            "name": u.name,
            "last_name": u.last_name,
            "avatar_path": u.avatar_path,
            "description": u.description,
            "role": role,
            "joined_at": joined_at.isoformat() if joined_at else None
        }
        for u, role, joined_at in rows 
    ]
    
    return data, 200, f"Участники получены"

async def delete_group(token: str, group_id: int, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        return None, 404, "Группа не найдена"

    if group.creator_id != user.id:
        return None, 403, "Только создатель группы может её удалить"

    messages_result = await db.execute(
        select(Message).where(Message.group_id == group_id)
    )
    messages = messages_result.scalars().all()

    for msg in messages:
        if msg.file_path:
            path = Path(msg.file_path)
            if path.exists() and path.is_file():
                path.unlink()

    if group.avatar_path:
        avatar_path = Path(group.avatar_path)
        if avatar_path.exists() and avatar_path.is_file():
            avatar_path.unlink()

    deleted_group_data = {
        "id": group.id,
        "name": group.name,
        "creator_id": group.creator_id
    }

    await db.delete(group)
    await db.commit()

    return deleted_group_data, 200, "Группа успешно удалена"

async def leave_from_group(token: str, group_id: int, db: AsyncSession):
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message
    
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    if not group:
        return None, 404, "Группа не найдена"
    
    member_result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user.id
        )
    )
    member = member_result.scalar_one_or_none()
    if not member:
        return None, 403, "Вы не состоите в этой группе"
        
    await db.delete(member)
    await db.commit()

    data = {
        "group_id": group_id,
        "user_id": user.id,
        "username": user.username
    }
    
    return data, 200, "Вы вышли из группы"
