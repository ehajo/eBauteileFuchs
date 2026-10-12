"""Exercise Alembic upgrades and downgrades against a disposable database only."""

from alembic import command
from alembic.config import Config

from ebauteilefuchs.config import Settings
from ebauteilefuchs.testing.migration_safety import (
    migration_test_environment,
    run_guarded_migration,
    temporary_migration_test_database,
)


def main() -> None:
    """Verify the complete migration chain without ever opening user data."""

    normal_settings = Settings()
    with temporary_migration_test_database(normal_settings) as database:
        with migration_test_environment(database, normal_settings):
            config = Config("alembic.ini")
            run_guarded_migration(
                command.upgrade,
                config,
                "head",
                database=database,
                normal_settings=normal_settings,
            )
            command.check(config)
            run_guarded_migration(
                command.downgrade,
                config,
                "base",
                database=database,
                normal_settings=normal_settings,
            )
            run_guarded_migration(
                command.upgrade,
                config,
                "head",
                database=database,
                normal_settings=normal_settings,
            )


if __name__ == "__main__":
    main()
