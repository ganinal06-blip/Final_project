import pytest
from src.bot_app import BotApp

class DummyBot:
    async def set_my_commands(self, *args, **kwargs):
        return True

    class session:
        @staticmethod
        async def close():
            return True

class DummyDispatcher:
    def include_router(self, *args, **kwargs):
        pass

    async def start_polling(self, bot):
        return True

async def dummy_init_db():
    return None

@pytest.mark.asyncio
async def test_bot_app_start(monkeypatch):
    monkeypatch.setattr("src.bot_app.Bot", lambda token: DummyBot())
    monkeypatch.setattr("src.bot_app.Dispatcher", lambda: DummyDispatcher())
    monkeypatch.setattr("src.bot_app.init_db", dummy_init_db)

    app = BotApp()
    await app.start()
