from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os


# Note: to avoid initializing an async engine during Alembic import/runtime we
# allow skipping engine creation by setting SKIP_ENGINE_INIT=1 in the
# environment. This prevents import-time side-effects while Alembic inspects
# models.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aiagent:StrongPassword123@postgres:5432/ai_team",
)

_SKIP = os.getenv("SKIP_ENGINE_INIT", "0") == "1"

if not _SKIP:
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
else:
    engine = None
    AsyncSessionLocal = None

Base = declarative_base()

async def get_db() -> AsyncSession:
    if AsyncSessionLocal is None:
        # When engine creation is skipped (e.g. during Alembic runs) this
        # function should not be used. Raise to make failures explicit.
        raise RuntimeError("Database engine not initialized")
    async with AsyncSessionLocal() as session:
        yield session
