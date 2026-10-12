from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from ebauteilefuchs.config import Settings
from ebauteilefuchs.testing.migration_safety import (
    migration_test_environment,
    run_guarded_migration,
    temporary_migration_test_database,
)


def test_empty_database_upgrades_and_downgrades() -> None:
    normal_settings = Settings()
    with temporary_migration_test_database(normal_settings) as database:
        with migration_test_environment(database, normal_settings):
            alembic_config = Config("alembic.ini")
            run_guarded_migration(
                command.upgrade,
                alembic_config,
                "head",
                database=database,
                normal_settings=normal_settings,
            )
            engine = create_engine(database.url)
            with engine.connect() as connection:
                revision = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
            assert revision == "0008_location_grid"
            inspector = inspect(engine)
            assert {
                "article",
                "article_attribute",
                "article_barcode",
                "category",
                "location",
                "location_type",
                "manufacturer",
                "inventory_balance",
                "inventory_movement",
                "inventory_transaction",
                "supplier",
                "supplier_part",
                "supplier_cache_entry",
            } <= set(inspector.get_table_names())
            with engine.connect() as connection:
                assert (
                    connection.execute(
                        text("SELECT COUNT(*) FROM location_type")
                    ).scalar()
                    == 8
                )
                assert (
                    connection.execute(
                        text(
                            "SELECT COUNT(*) FROM location "
                            "WHERE code = 'OHNE-LAGERPLATZ'"
                        )
                    ).scalar()
                    == 1
                )

            run_guarded_migration(
                command.downgrade,
                alembic_config,
                "base",
                database=database,
                normal_settings=normal_settings,
            )
            assert "alembic_version" in inspect(engine).get_table_names()
            with engine.connect() as connection:
                assert (
                    connection.execute(
                        text("SELECT COUNT(*) FROM alembic_version")
                    ).scalar()
                    == 0
                )
            engine.dispose()


def test_existing_m3_database_upgrades_to_m4_and_downgrades_without_data_loss() -> None:
    normal_settings = Settings()
    with temporary_migration_test_database(normal_settings) as database:
        with migration_test_environment(database, normal_settings):
            alembic_config = Config("alembic.ini")
            run_guarded_migration(
                command.upgrade,
                alembic_config,
                "0004_m3_inventory",
                database=database,
                normal_settings=normal_settings,
            )
            engine = create_engine(database.url)
            assert "location" in inspect(engine).get_table_names()
            assert "article" in inspect(engine).get_table_names()
            assert "inventory_balance" in inspect(engine).get_table_names()
            assert "supplier_cache_entry" not in inspect(engine).get_table_names()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO location (id, code, normalized_code, name, "
                        "location_type_id, parent_id, parent_scope, description, is_active, "
                        "qr_token, created_at, updated_at) VALUES "
                        "(:id, 'M2-ORT', 'm2-ort', 'Bestehender M2-Ort', :type_id, NULL, "
                        "'__root__', NULL, 1, 'existing-m2-token', CURRENT_TIMESTAMP, "
                        "CURRENT_TIMESTAMP)"
                    ),
                    {
                        "id": "51000000-0000-4000-8000-000000000001",
                        "type_id": "10000000-0000-4000-8000-000000000001",
                    },
                )
                connection.execute(
                    text(
                        "INSERT INTO article (id, name, manufacturer_id, "
                        "manufacturer_part_number, normalized_manufacturer_part_number, "
                        "category_id, description, datasheet_url, product_url, note, "
                        "search_text, is_active, created_at, updated_at) VALUES "
                        "(:id, 'Bestehender M2-Artikel', NULL, NULL, NULL, :category_id, "
                        "NULL, NULL, NULL, NULL, 'bestehender m2 artikel', 1, "
                        "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                    ),
                    {
                        "id": "52000000-0000-4000-8000-000000000001",
                        "category_id": "20000000-0000-4000-8000-000000000010",
                    },
                )

            run_guarded_migration(
                command.upgrade,
                alembic_config,
                "head",
                database=database,
                normal_settings=normal_settings,
            )
            with engine.connect() as connection:
                assert (
                    connection.execute(
                        text("SELECT version_num FROM alembic_version")
                    ).scalar_one()
                    == "0008_location_grid"
                )
                assert (
                    connection.execute(text("SELECT COUNT(*) FROM category")).scalar()
                    == 10
                )
                assert (
                    connection.execute(text("SELECT COUNT(*) FROM supplier")).scalar()
                    == 1
                )
                assert (
                    connection.execute(text("SELECT COUNT(*) FROM article")).scalar()
                    == 1
                )
                assert (
                    connection.execute(text("SELECT COUNT(*) FROM location")).scalar()
                    == 2
                )

            run_guarded_migration(
                command.downgrade,
                alembic_config,
                "0004_m3_inventory",
                database=database,
                normal_settings=normal_settings,
            )
            assert "location" in inspect(engine).get_table_names()
            assert "article" in inspect(engine).get_table_names()
            assert "inventory_balance" in inspect(engine).get_table_names()
            assert "supplier_cache_entry" not in inspect(engine).get_table_names()
            with engine.connect() as connection:
                assert (
                    connection.execute(text("SELECT COUNT(*) FROM article")).scalar()
                    == 1
                )
                assert (
                    connection.execute(text("SELECT COUNT(*) FROM location")).scalar()
                    == 1
                )
            engine.dispose()
