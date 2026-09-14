"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ebauteilefuchs import __version__
from ebauteilefuchs.api.errors import domain_error_response
from ebauteilefuchs.api.v1.articles import router as articles_api_router
from ebauteilefuchs.api.v1.health import router as health_router
from ebauteilefuchs.api.v1.inventory import router as inventory_api_router
from ebauteilefuchs.api.v1.locations import router as locations_api_router
from ebauteilefuchs.api.v1.search import router as search_api_router
from ebauteilefuchs.api.v1.suppliers import router as suppliers_api_router
from ebauteilefuchs.application.articles import ArticleService
from ebauteilefuchs.application.data_management import DataManagementService
from ebauteilefuchs.application.inventory import InventoryService
from ebauteilefuchs.application.locations import LocationService
from ebauteilefuchs.application.search import GlobalSearchService
from ebauteilefuchs.application.supplier_search import SupplierSearchService
from ebauteilefuchs.branding import BRANDING
from ebauteilefuchs.config import Settings, get_settings
from ebauteilefuchs.domain.errors import DomainError
from ebauteilefuchs.labels import ReportLabLabelRenderer
from ebauteilefuchs.logging_config import configure_logging
from ebauteilefuchs.main_paths import PACKAGE_DIR
from ebauteilefuchs.persistence.articles import SqlAlchemyArticleUnitOfWork
from ebauteilefuchs.persistence.data_management import (
    DatabaseWriteGate,
    SqliteDataManagementGateway,
)
from ebauteilefuchs.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from ebauteilefuchs.persistence.inventory import SqlAlchemyInventoryUnitOfWork
from ebauteilefuchs.persistence.locations import SqlAlchemyLocationUnitOfWork
from ebauteilefuchs.persistence.supplier_cache import SqlAlchemySupplierCache
from ebauteilefuchs.suppliers.mouser import MouserAdapter
from ebauteilefuchs.suppliers.mouser.client import MouserHttpClient
from ebauteilefuchs.web.articles import router as articles_web_router
from ebauteilefuchs.web.connection import router as connection_web_router
from ebauteilefuchs.web.data_management import router as data_management_web_router
from ebauteilefuchs.web.inventory import router as inventory_web_router
from ebauteilefuchs.web.locations import router as locations_web_router
from ebauteilefuchs.web.presentation import format_decimal
from ebauteilefuchs.web.routes import router as web_router
from ebauteilefuchs.web.search import router as search_web_router
from ebauteilefuchs.web.suppliers import router as suppliers_web_router


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
    app.state.inventory_service_factory = lambda: InventoryService(
        lambda: SqlAlchemyInventoryUnitOfWork(session_factory)
    )
    app.state.global_search_service_factory = lambda: GlobalSearchService(
        app.state.article_service_factory(),
        app.state.inventory_service_factory(),
        app.state.location_service_factory(),
    )
    app.state.qr_renderer = label_renderer
    mouser_key = (
        runtime_settings.mouser_api_key.get_secret_value()
        if runtime_settings.mouser_api_key
        else None
    )
    app.state.supplier_adapter = MouserAdapter(
        mouser_key,
        client=(
            MouserHttpClient(
                mouser_key,
                timeout_seconds=runtime_settings.mouser_timeout_seconds,
            )
            if mouser_key
            else None
        ),
    )
    app.state.supplier_search_service_factory = lambda: SupplierSearchService(
        app.state.article_service_factory(), app.state.supplier_adapter
    )
    app.state.supplier_cache = SqlAlchemySupplierCache(session_factory)
    app.state.database_write_gate = DatabaseWriteGate()
    app.state.data_management_service = DataManagementService(
        SqliteDataManagementGateway(
            runtime_settings, database_engine, app.state.database_write_gate
        )
    )
    app.state.templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
    app.state.templates.env.filters["number"] = format_decimal

    app.mount(
        "/static",
        StaticFiles(directory=PACKAGE_DIR / "static"),
        name="static",
    )
    app.include_router(web_router)
    app.include_router(locations_web_router)
    app.include_router(articles_web_router)
    app.include_router(inventory_web_router)
    app.include_router(suppliers_web_router)
    app.include_router(search_web_router)
    app.include_router(connection_web_router)
    app.include_router(data_management_web_router)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(locations_api_router, prefix="/api/v1")
    app.include_router(articles_api_router, prefix="/api/v1")
    app.include_router(inventory_api_router, prefix="/api/v1")
    app.include_router(suppliers_api_router, prefix="/api/v1")
    app.include_router(search_api_router, prefix="/api/v1")
    app.add_exception_handler(DomainError, domain_error_response)

    @app.middleware("http")
    async def reject_cross_origin_writes(request, call_next):
        is_write = request.method not in {"GET", "HEAD", "OPTIONS"}
        if is_write:
            origin = request.headers.get("origin")
            if origin:
                parsed = urlsplit(origin)
                host = request.headers.get("host", "")
                if parsed.netloc.casefold() != host.casefold():
                    return JSONResponse(
                        {"detail": "Die Anfrage stammt von einer fremden Website."},
                        status_code=403,
                    )
            if not app.state.database_write_gate.enter_write():
                return JSONResponse(
                    {
                        "detail": "Die Datenbank wird gerade wiederhergestellt. "
                        "Versuche es nach dem Neustart erneut."
                    },
                    status_code=503,
                )
        try:
            return await call_next(request)
        finally:
            if is_write:
                app.state.database_write_gate.leave_write()

    return app


app = create_app()
