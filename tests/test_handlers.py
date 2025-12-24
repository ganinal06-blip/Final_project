import pytest
from types import SimpleNamespace
from src.handlers import cmd_start, universal_logger_and_handlers

class DummyBot:
    async def get_file(self, *args, **kwargs):
        return SimpleNamespace(file_path="x")

    async def download_file(self, *args, **kwargs):
        return None

class DummyMessage:
    def __init__(self, text=None, chat_type="private"):
        self.text = text
        self.chat = SimpleNamespace(id=1, type=chat_type)
        self.from_user = SimpleNamespace(id=1, username="tester")
        self.bot = DummyBot()
        self.document = None
        self.new_chat_members = None

    async def answer(self, text):
        self.last_answer = text

@pytest.mark.asyncio
async def test_cmd_start():
    msg = DummyMessage()
    await cmd_start(msg)
    assert "Привет" in msg.last_answer

@pytest.mark.asyncio
async def test_universal_handler_clean_private():
    msg = DummyMessage(text="/clean", chat_type="private")
    await universal_logger_and_handlers(msg)
    assert "только в группе" in msg.last_answer.lower()
