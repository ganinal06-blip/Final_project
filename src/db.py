from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from .config import settings

def ensure_sqlite_dir(db_url: str):
    if db_url.startswith("sqlite"):
        parts = db_url.split("///", 1)
        if len(parts) == 2:
            path_str = parts[1]
            p = Path(path_str)
            parent = p.parent
            if not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)

ensure_sqlite_dir(settings.DATABASE_URL)

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    from .models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)