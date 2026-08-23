from pathlib import Path

from sqlalchemy import text

from ebauteilefuchs.config import Settings
from ebauteilefuchs.persistence.database import create_database_engine


def test_sqlite_engine_enables_required_pragmas(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        database_url=f"sqlite+pysqlite:///{(tmp_path / 'pragmas.db').as_posix()}",
    )
    engine = create_database_engine(settings)

    with engine.connect() as connection:
        foreign_keys = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
        busy_timeout = connection.execute(text("PRAGMA busy_timeout")).scalar_one()
        journal_mode = connection.execute(text("PRAGMA journal_mode")).scalar_one()

    engine.dispose()
    assert foreign_keys == 1
    assert busy_timeout == 5_000
    assert journal_mode == "wal"
