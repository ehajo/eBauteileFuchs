"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ebauteilefuchs import __version__
from ebauteilefuchs.api.v1.health import router as health_router
from ebauteilefuchs.branding import BRANDING
from ebauteilefuchs.config import Settings, get_settings
from ebauteilefuchs.logging_config import configure_logging
from ebauteilefuchs.persistence.database import create_database_engine
from ebauteilefuchs.web.routes import router as web_router

PACKAGE_DIR = Path(__file__).resolve().parent


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)
    database_engine = create_database_engine(runtime_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        database_engine.dispose()

    app = FastAPI(
        title=BRANDING.product_name,
        summary=BRANDING.tagline,
        version=__version__,
        lifespan=lifespan,
    )
    app.state.branding = BRANDING
    app.state.database_engine = database_engine
    app.state.settings = runtime_settings
    app.state.templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")

    app.mount(
        "/static",
        StaticFiles(directory=PACKAGE_DIR / "static"),
        name="static",
    )
    app.include_router(web_router)
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
