import pytest
from src.main import main

class DummyBotApp:
    async def start(self):
        return True

@pytest.mark.asyncio
async def test_main_runs(monkeypatch):
    monkeypatch.setattr("src.main.BotApp", lambda: DummyBotApp())
    await main()
