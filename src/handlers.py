import logging
from typing import List
from io import BytesIO

from aiogram import types
from aiogram import Router
from aiogram.filters import Command, CommandStart

from .config import settings
from .repository import MemberRepository

logger = logging.getLogger(__name__)
router = Router()
member_repo = MemberRepository()


# Команда /start
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! В личке пришлите .txt со списком разрешённых (по одному в строке). "
        "В группе используйте команду /clean."
    )


# Обработчик всех сообщений
@router.message()
async def universal_logger_and_handlers(message: types.Message):
    # Логирование всех входящих сообщений и апдейтов
    logger.info(
        "INCOMING: update_id=%s chat_id=%s chat_type=%s from=%s text=%s new_members=%s",
        getattr(message, "message_id", None),
        message.chat.id if message.chat else None,
        message.chat.type if message.chat else None,
        getattr(message.from_user, "id", None),
        getattr(message, "text", None),
        [u.id for u in (message.new_chat_members or [])] if message.new_chat_members else None
    )

    # Обработка документов
    if message.document:
        doc: types.Document = message.document
        if doc.mime_type in ("text/plain", "application/octet-stream", "text/csv"):
            try:
                bot_client = message.bot
                file_obj = await bot_client.get_file(doc.file_id)
                bio = BytesIO()
                await bot_client.download_file(file_obj.file_path, destination=bio)
                bio.seek(0)
                content = bio.read()

                moderation = getattr(router, "_moderation", None)
                if moderation is None:
                    await message.answer("Сервис модерации не настроен.")
                    return

                count = await moderation.load_allowed_from_bytes(content)
                await message.answer(f"Список разрешенных пользователей обновлен: {count} записей.")
                logger.info("Allowed list updated: %d records (by %s)", count, message.from_user.id)
            except Exception as e:
                logger.exception("Ошибка при обработке документа: %s", e)
                await message.answer(f"Не удалось обработать файл: {e}")
        else:
            await message.answer("Пожалуйста, пришлите .txt файл со списком разрешённых.")
        return

    # Обработка новых участников в чате
    new_members: List[types.User] = message.new_chat_members or []
    if new_members:
        for u in new_members:
            logger.info("NEW_MEMBER: id=%s username=%s chat=%s", u.id, u.username, message.chat.id)
            await member_repo.upsert_member(chat_id=str(message.chat.id), user_id=str(u.id), username=u.username)

        moderation = getattr(router, "_moderation", None)
        if moderation:
            members_for_check = [{"id": u.id, "username": u.username} for u in new_members]
            unauthorized = await moderation.filter_unauthorized(members_for_check)
            if unauthorized:
                await moderation.ban_users(chat_id=message.chat.id, users=unauthorized)

    # Обновление базы участников при любом сообщении в группе
    if message.chat and message.chat.type in ("group", "supergroup"):
        user = message.from_user
        if user:
            await member_repo.upsert_member(chat_id=str(message.chat.id), user_id=str(user.id), username=user.username)
# Обработка команды /clean
    text = (message.text or "").strip()
    if text:
        lower = text.split()[0].lower()
        if lower.startswith("/clean"):
            if message.chat.type not in ("group", "supergroup"):
                await message.answer("Команда /clean работает только в группе.")
                return

            if settings.ADMIN_CHAT_ID and message.from_user.id != settings.ADMIN_CHAT_ID:
                await message.answer("Только админ может запускать /clean.")
                return

            await message.answer("Запускаю очистку... (проверяю известных участников)")
            moderation = getattr(router, "_moderation", None)
            if moderation is None:
                await message.answer("Сервис модерации не доступен.")
                return

            res = await moderation.clean_chat(chat_id=int(message.chat.id))
            await message.answer(f"Проверено: {res['checked']}. Найдено: {res['to_ban']}. Забанено: {res['banned']}.")
            return

    return