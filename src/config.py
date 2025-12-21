import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

env_path = Path(".") / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
    ADMIN_CHAT_ID: Optional[int] = None
    _admin = os.getenv("ADMIN_CHAT_ID", "").strip()
    if _admin:
        try:
            ADMIN_CHAT_ID = int(_admin)
        except Exception:
            ADMIN_CHAT_ID = None

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/db.sqlite3").strip()
    CHECK_INTERVAL_SECONDS: int = int(os.getenv("CHECK_INTERVAL_SECONDS", "3600"))
    AUTO_CLEAN_FORCE: bool = os.getenv("AUTO_CLEAN_FORCE", "false").lower() in ("1","true","yes")

settings = Settings()