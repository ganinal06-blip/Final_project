import pytest
import pytest_asyncio
from sqlalchemy import select
from src.db import AsyncSessionLocal, engine
from src.models import Base, ActionLog
from src.repository import AllowedUserRepository, MemberRepository, ActionLogRepository

@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest.mark.asyncio
async def test_allowed_repo_set_and_list():
    repo = AllowedUserRepository()
    await repo.set_users(["@masha", "123"])
    identifiers = await repo.list_identifiers()
    assert "@masha" in identifiers
    assert "123" in identifiers

@pytest.mark.asyncio
async def test_allowed_repo_overwrite():
    repo = AllowedUserRepository()
    await repo.set_users(["@masha"])
    await repo.set_users(["@liza"])
    identifiers = await repo.list_identifiers()
    assert identifiers == ["@liza"]

@pytest.mark.asyncio
async def test_member_repo_upsert_and_list():
    repo = MemberRepository()
    await repo.upsert_member(chat_id="1", user_id="42", username="liza")
    members = await repo.list_members_by_chat("1")
    assert len(members) == 1
    assert members[0]["user_id"] == "42"
    assert members[0]["username"] == "liza"

@pytest.mark.asyncio
async def test_member_repo_upsert_updates_username():
    repo = MemberRepository()
    await repo.upsert_member(chat_id="1", user_id="42", username="liza")
    await repo.upsert_member(chat_id="1", user_id="42", username="liza")
    members = await repo.list_members_by_chat("1")
    assert members[0]["username"] == "liza"

@pytest.mark.asyncio
async def test_member_repo_remove():
    repo = MemberRepository()
    await repo.upsert_member(chat_id="1", user_id="42", username="liza")
    await repo.remove_member(chat_id="1", user_id="42")
    members = await repo.list_members_by_chat("1")
    assert len(members) == 0

@pytest.mark.asyncio
async def test_member_repo_list_known_chats():
    repo = MemberRepository()
    await repo.upsert_member(chat_id="1", user_id="42", username="liza")
    await repo.upsert_member(chat_id="2", user_id="43", username="masha")
    chats = await repo.list_known_chats()
    assert "1" in chats
    assert "2" in chats

@pytest.mark.asyncio
async def test_action_log_repo():
    repo = ActionLogRepository()
    await repo.log(chat_id="1", user_identifier="@liza", action="banned")
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(ActionLog).where(ActionLog.chat_id=="1"))
        logs = q.scalars().all()
        assert len(logs) == 1
        log = logs[0]
        assert log.user_identifier == "@liza"
        assert log.action == "banned"

@pytest.mark.asyncio
async def test_action_log_with_reason():
    repo = ActionLogRepository()
    await repo.log(chat_id="2", user_identifier="@liza", action="ban_failed", reason="not participant")
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(ActionLog).where(ActionLog.chat_id=="2"))
        logs = q.scalars().all()
        assert logs[0].reason == "not participant"
