from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_baseline_migration_upgrades_and_downgrades(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("EBAUTEILEFUCHS_APP_ENV", "test")
    monkeypatch.setenv("EBAUTEILEFUCHS_DATABASE_URL", database_url)
    alembic_config = Config("alembic.ini")

    command.upgrade(alembic_config, "head")

    engine = create_engine(database_url)
    with engine.connect() as connection:
        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    assert revision == "0001_m0_baseline"

    command.downgrade(alembic_config, "base")
    assert "alembic_version" in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT COUNT(*) FROM alembic_version")).scalar()
            == 0
        )
    engine.dispose()
