"""Create a consistent eBauteileFuchs backup without exposing secrets."""

from ebauteilefuchs.config import get_settings
from ebauteilefuchs.persistence.data_management import SqliteDataManagementGateway
from ebauteilefuchs.persistence.database import create_database_engine


def main() -> None:
    settings = get_settings()
    engine = create_database_engine(settings)
    try:
        backup = SqliteDataManagementGateway(settings, engine).create_backup()
    finally:
        engine.dispose()
    print(f"Sicherung erstellt: {backup.path}")


if __name__ == "__main__":
    main()
