"""SQLAlchemy and SQLite foundation."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ebauteilefuchs.config import Settings


class Base(DeclarativeBase):
    """Base class for ORM mappings introduced in later milestones."""


def _is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite")


def ensure_sqlite_parent(database_url: str) -> None:
    """Create the parent directory for a file-based SQLite database URL."""
    prefix = "sqlite+pysqlite:///"
    if not database_url.startswith(prefix):
        return
    path_value = database_url.removeprefix(prefix)
    if path_value == ":memory:" or path_value.startswith("file:"):
        return
    Path(path_value).parent.mkdir(parents=True, exist_ok=True)


def create_database_engine(settings: Settings) -> Engine:
    """Create an engine with safe SQLite defaults for local use."""

    database_url = settings.resolved_database_url
    ensure_sqlite_parent(database_url)
    kwargs: dict[str, Any] = {"pool_pre_ping": True}

    if _is_sqlite_url(database_url):
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 5}
        if database_url.endswith(":memory:"):
            kwargs["poolclass"] = StaticPool

    engine = create_engine(database_url, **kwargs)

    if _is_sqlite_url(database_url):

        @event.listens_for(engine, "connect")
        def set_sqlite_pragmas(dbapi_connection: Any, _: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Yield a session and apply explicit commit/rollback boundaries."""

    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database(engine: Engine) -> None:
    """Raise if the configured database cannot answer a basic query."""

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
