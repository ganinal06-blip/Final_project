import logging
from typing import List, Dict, Any, Iterable
import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from .repository import AllowedUserRepository, ActionLogRepository, MemberRepository
from .utils import parse_allowed_file_bytes
from .config import settings

logger = logging.getLogger(__name__)

class ModerationService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.allowed_repo = AllowedUserRepository()
        self.log_repo = ActionLogRepository()
        self.member_repo = MemberRepository()

    async def load_allowed_from_bytes(self, content: bytes) -> int:
        identifiers = parse_allowed_file_bytes(content)
        await self.allowed_repo.set_users(identifiers)
        logger.info("Allowed users set: %d entries", len(identifiers))
        return len(identifiers)

    async def get_allowed_identifiers(self) -> List[str]:
        return await self.allowed_repo.list_identifiers()

    def _normalize_allowed_set(self, allowed_list: Iterable[str]) -> set:
        s = set()
        for a in allowed_list:
            if not a:
                continue
            a_str = a.strip()
            if a_str.startswith("@"):
                s.add(a_str.lower())
                s.add(a_str[1:].lower())
            elif a_str.isdigit():
                s.add(a_str)
            else:
                s.add(a_str.lower())
        return s

    def _make_idents_for_member_record(self, member: Dict[str, Any]) -> set:
        idents = set()
        uname = member.get("username")
        uid_val = member.get("user_id") if member.get("user_id") is not None else member.get("id")
        if uname:
            try:
                uname_l = uname.lower()
            except Exception:
                uname_l = str(uname)
            idents.add(f"@{uname_l}")
            idents.add(uname_l)
        if uid_val is not None:
            idents.add(str(uid_val))
        return idents

    async def filter_unauthorized(self, members: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        allowed = await self.get_allowed_identifiers()
        allowed_set = self._normalize_allowed_set(allowed)
        unauthorized: List[Dict[str, Any]] = []
        for mem in members:
            idents = self._make_idents_for_member_record(mem)
            if idents & allowed_set:
                continue
            uid = mem.get("id") if mem.get("id") is not None else mem.get("user_id")
            if uid is None:
                logger.warning("Member record has no id: %r", mem)
                continue
            try:
                uid_int = int(uid)
            except Exception:
                logger.warning("Member id not int, skip: %r", uid)
                continue
            identifier = f"@{mem['username']}" if mem.get("username") else str(uid_int)
            unauthorized.append({"id": uid_int, "identifier": identifier})
        return unauthorized
    async def ban_users(self, chat_id: int, users: List[Dict[str, Any]]) -> int:
            banned = 0
            for u in users:
                uid = u.get("id")
                identifier = u.get("identifier", str(uid))
                try:
                    logger.info("Attempting ban: chat=%s user=%s identifier=%s", chat_id, uid, identifier)
                    await self.bot.ban_chat_member(chat_id=chat_id, user_id=int(uid))
                    await self.log_repo.log(chat_id=str(chat_id), user_identifier=str(identifier), action="banned")
                    banned += 1
                    logger.info("Banned user %s in chat %s", identifier, chat_id)
                    await asyncio.sleep(0.2)
                except TelegramBadRequest as e:
                    text = str(e).lower()
                    
                    if "user_not_participant" in text or "user not participant" in text or "user not found" in text:
                        logger.info("User %s is not participant in chat %s — removing from members DB.", identifier,
                                    chat_id)
                        try:
                            await self.member_repo.remove_member(chat_id=str(chat_id), user_id=str(uid))
                            await self.log_repo.log(chat_id=str(chat_id), user_identifier=str(identifier),
                                                    action="already_left")
                        except Exception:
                            logger.exception("Failed removing member record for %s in chat %s", identifier, chat_id)
                        continue

                    logger.exception("Failed to ban %s in chat %s: %s", identifier, chat_id, e)
                    await self.log_repo.log(chat_id=str(chat_id), user_identifier=str(identifier), action="ban_failed",
                                            reason=str(e))
                    if settings.ADMIN_CHAT_ID:
                        try:
                            await self.bot.send_message(settings.ADMIN_CHAT_ID,
                                                        f"Ошибка при бане {identifier} в чате {chat_id}: {e}")
                        except Exception:
                            logger.exception("Failed to notify admin")
                except Exception as e:
                    logger.exception("Failed to ban %s in chat %s: %s", identifier, chat_id, e)
                    await self.log_repo.log(chat_id=str(chat_id), user_identifier=str(identifier), action="ban_failed",
                                            reason=str(e))
                    if settings.ADMIN_CHAT_ID:
                        try:
                            await self.bot.send_message(settings.ADMIN_CHAT_ID,
                                                        f"Ошибка при бане {identifier} в чате {chat_id}: {e}")
                        except Exception:
                            logger.exception("Failed to notify admin")
            return banned
    async def clean_chat(self, chat_id: int) -> Dict[str, int]:
        logger.info("Starting clean_chat for chat=%s", chat_id)
        members = await self.member_repo.list_members_by_chat(str(chat_id))
        logger.debug("Known members for chat %s: %s", chat_id, members)
        allowed = await self.get_allowed_identifiers()
        allowed_set = self._normalize_allowed_set(allowed)
        to_ban: List[Dict[str, Any]] = []
        for m in members:
            idents = self._make_idents_for_member_record({"username": m.get("username"), "user_id": m.get("user_id")})
            if idents & allowed_set:
                continue
            try:
                uid_int = int(m["user_id"])
            except Exception:
                logger.warning("Skip member with invalid user_id: %r", m.get("user_id"))
                continue
            identifier = next(iter(idents)) if idents else str(uid_int)
            to_ban.append({"id": uid_int, "identifier": identifier})
        logger.info("Clean candidate list for chat %s: to_ban=%d checked=%d", chat_id, len(to_ban), len(members))
        banned = await self.ban_users(chat_id=chat_id, users=to_ban)
        logger.info("Clean finished for chat %s: checked=%d to_ban=%d banned=%d", chat_id, len(members), len(to_ban),
                    banned)
        return {"checked": len(members), "to_ban": len(to_ban), "banned": banned}