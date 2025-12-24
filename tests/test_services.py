import pytest
from aiogram.exceptions import TelegramBadRequest
from src.services import ModerationService

class FakeAllowedRepo:
    def __init__(self, idents):
        self._idents = list(idents)

    async def list_identifiers(self):
        return list(self._idents)

    async def set_users(self, identifiers):
        self._idents = list(identifiers)


class FakeMemberRepo:
    def __init__(self, members=None):
        self._members = members or []
        self.removed = []

    async def list_members_by_chat(self, chat_id: str):
        return list(self._members)

    async def remove_member(self, chat_id: str, user_id: str):
        self.removed.append((chat_id, str(user_id)))
        self._members = [
            m for m in self._members if str(m.get("user_id")) != str(user_id)
        ]


class FakeLogRepo:
    def __init__(self):
        self.records = []

    async def log(self, chat_id, user_identifier, action, reason=None):
        self.records.append(
            {"chat_id": str(chat_id), "user": user_identifier, "action": action, "reason": reason}
        )


class DummyBot:
    async def ban_chat_member(self, chat_id, user_id):
        return True

@pytest.mark.asyncio
async def test_filter_unauthorized_by_username_and_id():
    bot = DummyBot()
    svc = ModerationService(bot)
    svc.allowed_repo = FakeAllowedRepo(["@gooduser", "42"])
    members = [
        {"id": 42, "username": "gooduser"},
        {"id": "43", "username": "other"},
        {"id": 99, "username": "baduser"},
    ]
    res = await svc.filter_unauthorized(members)
    ids = {item["id"] for item in res}
    assert "43" in ids or 43 in ids
    assert 99 in ids


@pytest.mark.asyncio
async def test_clean_chat_candidates_and_ban_called():
    bot = DummyBot()
    svc = ModerationService(bot)
    svc.allowed_repo = FakeAllowedRepo(["@allowed"])
    svc.member_repo = FakeMemberRepo([
        {"user_id": "1", "username": "allowed"},
        {"user_id": "2", "username": "stranger"},
    ])
    called = {}

    async def fake_ban(chat_id, users):
        called['chat_id'] = chat_id
        called['users'] = users
        return len(users)

    svc.ban_users = fake_ban
    res = await svc.clean_chat(chat_id="999")
    assert res["checked"] == 2
    assert res["to_ban"] == 1
    assert res["banned"] == 1
    assert called.get('chat_id') == "999"
    assert isinstance(called.get('users'), list)
    assert str(called['users'][0]['id']) == "2"


@pytest.mark.asyncio
async def test_ban_users_with_failures():
    class FakeBotFail(DummyBot):
        def __init__(self, fail_ids=None):
            self.fail_ids = set(str(i) for i in (fail_ids or []))
            self.banned = []

        async def ban_chat_member(self, chat_id, user_id):
            if str(user_id) in self.fail_ids:
                raise TelegramBadRequest("USER_NOT_PARTICIPANT")
            self.banned.append((chat_id, str(user_id)))
            return True

    bot = FakeBotFail(fail_ids=["2"])
    svc = ModerationService(bot)
    svc.member_repo = FakeMemberRepo()
    svc.log_repo = FakeLogRepo()

    users = [
        {"id": "1", "identifier": "@Masha"},
        {"id": "2", "identifier": "@Liza"}
    ]

    banned_count = await svc.ban_users(chat_id="999", users=users)
    assert banned_count == 1

    actions = [r["action"] for r in svc.log_repo.records]
    assert "banned" in actions
    assert "already_left" in actions or "ban_failed" in actions
