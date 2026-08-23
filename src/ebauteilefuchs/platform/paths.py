"""Cross-platform runtime path resolution."""

import os
import sys
from pathlib import Path


def default_data_dir(app_env: str) -> Path:
    """Return a writable default data directory for the current platform."""

    if app_env in {"development", "test"}:
        return Path.cwd() / "data"

    if sys.platform == "win32":
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "eBauteileFuchs"
        return Path.home() / "AppData" / "Local" / "eBauteileFuchs"

    xdg_data_home = os.getenv("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "ebauteilefuchs"
    return Path.home() / ".local" / "share" / "ebauteilefuchs"
