"""Restore a verified eBauteileFuchs backup after explicit confirmation."""

import argparse
from pathlib import Path

from ebauteilefuchs.application.data_management import DataManagementError
from ebauteilefuchs.config import get_settings
from ebauteilefuchs.persistence.data_management import SqliteDataManagementGateway
from ebauteilefuchs.persistence.database import create_database_engine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="eBauteileFuchs-Sicherung wiederherstellen"
    )
    parser.add_argument("backup", type=Path, help="geprüfte ZIP-Sicherung")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="bestätigt, dass die aktuelle Datenbank ersetzt werden darf",
    )
    args = parser.parse_args()
    if not args.confirm:
        parser.error("Der Restore ersetzt Daten. Erneut mit --confirm ausführen.")
    if not args.backup.is_file():
        parser.error("Die angegebene Sicherungsdatei existiert nicht.")

    settings = get_settings()
    engine = create_database_engine(settings)
    try:
        gateway = SqliteDataManagementGateway(settings, engine)
        preview = gateway.stage_restore(args.backup.resolve())
        result = gateway.restore(preview.token)
    except DataManagementError as exc:
        parser.error(str(exc))
    finally:
        engine.dispose()
    print(f"Wiederherstellung abgeschlossen. Vorsicherung: {result.safety_backup.path}")


if __name__ == "__main__":
    main()
