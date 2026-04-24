from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
import logging


logger = logging.getLogger(__name__)


# Note: to avoid initializing an async engine during Alembic import/runtime we
# allow skipping engine creation by setting SKIP_ENGINE_INIT=1 in the
# environment. This prevents import-time side-effects while Alembic inspects
# models.
_raw_db = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aiagent:StrongPassword123@postgres:5432/ai_team",
)


def _ensure_asyncpg(url: str) -> str:
    """Ensure the SQLAlchemy URL uses the asyncpg driver.

    If a user provided a sync URL like 'postgresql://' or 'postgres://',
    convert it to the async form 'postgresql+asyncpg://'. This is a
    best-effort normalization to avoid SQLAlchemy selecting the sync
    psycopg2 driver when an async engine is expected.
    """
    # Already the preferred asyncpg form
    if url.startswith("postgresql+asyncpg://"):
        return url
    # Handle common sync forms and explicit psycopg2 driver specs.
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        logger.warning("Normalizing DATABASE_URL from sync 'postgres' scheme to 'postgresql+asyncpg://'")
        return url.replace("postgres://", "postgresql+asyncpg://", 1).replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )
    # If someone provided a URL like 'postgresql+psycopg2://...' or any
    # 'postgresql+<driver>://' variant that is not asyncpg, switch it.
    if url.startswith("postgresql+"):
        # find until :// and replace the driver part
        try:
            prefix, rest = url.split("://", 1)
        except ValueError:
            return url
        if not prefix.endswith("+asyncpg"):
            logger.warning(
                "Normalizing DATABASE_URL driver from '%s' to 'postgresql+asyncpg'",
                prefix,
            )
            return "postgresql+asyncpg://" + rest
    # not a postgres URL, return as-is
    return url


DATABASE_URL = _ensure_asyncpg(_raw_db)

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
