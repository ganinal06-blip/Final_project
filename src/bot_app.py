import sys

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from .config import settings
from .services import ModerationService
from .handlers import router as app_router
from .db import init_db


# Настройка логирования
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class BotApp:
    def __init__(self):

        # Инициализация основных объектов бота
        self.bot = Bot(token=settings.BOT_TOKEN)
        self.dp = Dispatcher()
        self.moderation = ModerationService(self.bot)
        self.router = app_router
        self.dp.include_router(self.router)

    async def start(self):

        # Подготовка окружения
        await init_db()

        # Регистрация команд бота
        try:
            await self.bot.set_my_commands([
                BotCommand(command="start", description="Запустить бота"),
                BotCommand(command="clean", description="Проверить и удалить незнакомцев"),
            ])
            logger.info("Bot commands set")
        except Exception:
            logger.exception("Failed to set bot commands")

        # Передача сервисов в обработчики
        setattr(self.router, "_moderation", self.moderation)

        # Настройка логов aiogram
        logging.getLogger("aiogram").setLevel(logging.DEBUG)

        # Запуск бота
        try:
            logger.info("Запуск бота (polling)...")
            await self.dp.start_polling(self.bot)
        finally:
            await self.bot.session.close()