"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ebauteilefuchs import __version__
from ebauteilefuchs.api.errors import domain_error_response
from ebauteilefuchs.api.v1.articles import router as articles_api_router
from ebauteilefuchs.api.v1.health import router as health_router
from ebauteilefuchs.api.v1.locations import router as locations_api_router
from ebauteilefuchs.application.articles import ArticleService
from ebauteilefuchs.application.locations import LocationService
from ebauteilefuchs.branding import BRANDING
from ebauteilefuchs.config import Settings, get_settings
from ebauteilefuchs.domain.errors import DomainError
from ebauteilefuchs.labels import ReportLabLabelRenderer
from ebauteilefuchs.logging_config import configure_logging
from ebauteilefuchs.persistence.articles import SqlAlchemyArticleUnitOfWork
from ebauteilefuchs.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from ebauteilefuchs.persistence.locations import SqlAlchemyLocationUnitOfWork
from ebauteilefuchs.web.articles import router as articles_web_router
from ebauteilefuchs.web.locations import router as locations_web_router
from ebauteilefuchs.web.routes import router as web_router

PACKAGE_DIR = Path(__file__).resolve().parent


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)
    database_engine = create_database_engine(runtime_settings)
    session_factory = create_session_factory(database_engine)
    label_renderer = ReportLabLabelRenderer()

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
    app.state.location_service_factory = lambda: LocationService(
        lambda: SqlAlchemyLocationUnitOfWork(session_factory), label_renderer
    )
    app.state.article_service_factory = lambda: ArticleService(
        lambda: SqlAlchemyArticleUnitOfWork(session_factory)
    )
    app.state.templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")

    app.mount(
        "/static",
        StaticFiles(directory=PACKAGE_DIR / "static"),
        name="static",
    )
    app.include_router(web_router)
    app.include_router(locations_web_router)
    app.include_router(articles_web_router)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(locations_api_router, prefix="/api/v1")
    app.include_router(articles_api_router, prefix="/api/v1")
    app.add_exception_handler(DomainError, domain_error_response)

    @app.middleware("http")
    async def reject_cross_origin_writes(request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin:
                parsed = urlsplit(origin)
                host = request.headers.get("host", "")
                if parsed.netloc.casefold() != host.casefold():
                    return JSONResponse(
                        {"detail": "Die Anfrage stammt von einer fremden Website."},
                        status_code=403,
                    )
        return await call_next(request)

    return app


app = create_app()
