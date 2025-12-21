repository.py
from typing import List, Optional
from sqlalchemy import select, delete, distinct
from .models import AllowedUser, ActionLog, Member
from .db import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

class AllowedUserRepository:
    async def set_users(self, identifiers: List[str]) -> None:
        async with AsyncSessionLocal() as session:
            await session.execute(delete(AllowedUser))
            objs = [AllowedUser(user_identifier=ident) for ident in identifiers]
            session.add_all(objs)
            await session.commit()

    async def list_identifiers(self) -> List[str]:
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(AllowedUser.user_identifier))
            rows = q.scalars().all()
            return list(rows)

class ActionLogRepository:
    async def log(self, chat_id: str, user_identifier: str, action: str, reason: Optional[str] = None):
        async with AsyncSessionLocal() as session:
            log = ActionLog(chat_id=str(chat_id), user_identifier=user_identifier, action=action, reason=reason)
            session.add(log)
            await session.commit()

class MemberRepository:
    async def upsert_member(self, chat_id: str, user_id: str, username: Optional[str]):
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(Member).where(Member.chat_id == str(chat_id), Member.user_id == str(user_id)))
            obj = q.scalars().first()
            if obj:
                obj.username = username
            else:
                obj = Member(chat_id=str(chat_id), user_id=str(user_id), username=username)
                session.add(obj)
            await session.commit()

    async def list_members_by_chat(self, chat_id: str) -> List[dict]:
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(Member).where(Member.chat_id == str(chat_id)))
            rows = q.scalars().all()
            return [{"user_id": r.user_id, "username": r.username} for r in rows]

    async def remove_member(self, chat_id: str, user_id: str):
        async with AsyncSessionLocal() as session:
            await session.execute(delete(Member).where(Member.chat_id == str(chat_id), Member.user_id == str(user_id)))
            await session.commit()

    async def list_known_chats(self) -> List[str]:
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(distinct(Member.chat_id)))
            rows = q.scalars().all()
            return [str(r) for r in rows]