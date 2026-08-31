"""Command-line application entry point."""

import logging

import uvicorn

from ebauteilefuchs.branding import BRANDING
from ebauteilefuchs.config import get_settings
from ebauteilefuchs.logging_config import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = logging.getLogger("ebauteilefuchs.startup")
    browser_host = "127.0.0.1" if settings.host == "0.0.0.0" else settings.host
    logger.info("%s – %s", BRANDING.product_name, BRANDING.tagline)
    logger.info("%s", BRANDING.attribution)
    logger.info("Datenverzeichnis: %s", settings.resolved_data_dir)
    logger.info(
        "Lokaler Aufruf: %s://%s:%d",
        settings.url_scheme,
        browser_host,
        settings.port,
    )
    uvicorn.run(
        "ebauteilefuchs.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        ssl_certfile=str(settings.ssl_certfile) if settings.ssl_certfile else None,
        ssl_keyfile=str(settings.ssl_keyfile) if settings.ssl_keyfile else None,
    )


if __name__ == "__main__":
    main()
