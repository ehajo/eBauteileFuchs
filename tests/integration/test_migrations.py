from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_empty_database_upgrades_and_downgrades(monkeypatch, tmp_path: Path) -> None:
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
    assert revision == "0003_m2_articles"
    inspector = inspect(engine)
    assert {
        "article",
        "article_attribute",
        "category",
        "location",
        "location_type",
        "manufacturer",
        "supplier",
        "supplier_part",
    } <= set(inspector.get_table_names())
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT COUNT(*) FROM location_type")).scalar() == 8
        )

    command.downgrade(alembic_config, "base")
    assert "alembic_version" in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT COUNT(*) FROM alembic_version")).scalar()
            == 0
        )
    engine.dispose()


def test_existing_m1_database_upgrades_to_m2(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "new-data-directory" / "existing-m1.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("EBAUTEILEFUCHS_APP_ENV", "test")
    monkeypatch.setenv("EBAUTEILEFUCHS_DATABASE_URL", database_url)
    alembic_config = Config("alembic.ini")

    command.upgrade(alembic_config, "0002_m1_locations")
    engine = create_engine(database_url)
    assert "location" in inspect(engine).get_table_names()
    assert "article" not in inspect(engine).get_table_names()

    command.upgrade(alembic_config, "head")
    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            == "0003_m2_articles"
        )
        assert connection.execute(text("SELECT COUNT(*) FROM category")).scalar() == 10
        assert connection.execute(text("SELECT COUNT(*) FROM supplier")).scalar() == 1

    command.downgrade(alembic_config, "0002_m1_locations")
    assert "location" in inspect(engine).get_table_names()
    assert "article" not in inspect(engine).get_table_names()
    engine.dispose()
