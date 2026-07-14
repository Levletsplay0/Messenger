from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Group, GroupMember
from services.user import get_user_by_token

async def check_permissions_ws(token: str, group_id: int, db: AsyncSession):    
    user, status_code, message = await get_user_by_token(token, db)
    if not user:
        return None, status_code, message
    
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        return None, 404, "Такой группы не существует"

    member_res = await db.execute(select(GroupMember).where(
        GroupMember.group_id == group_id, 
        GroupMember.user_id == user.id
    ))
    
    if not member_res.scalar_one_or_none():
        return None, 403, "Только участники группы могут присоединяться"
    
    
    return user, 200, f"Вы состоите в группе: {group_id}"
