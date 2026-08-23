from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from ebauteilefuchs.config import Settings
from ebauteilefuchs.main import create_app
from ebauteilefuchs.persistence.database import Base, create_database_engine
from ebauteilefuchs.persistence.location_types import SYSTEM_LOCATION_TYPES
from ebauteilefuchs.persistence.models import LocationTypeModel


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        app_env="test",
        data_dir=tmp_path,
        database_url=f"sqlite+pysqlite:///{(tmp_path / 'test.db').as_posix()}",
        log_level="WARNING",
    )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client(test_settings: Settings) -> AsyncIterator[AsyncClient]:
    engine = create_database_engine(test_settings)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            LocationTypeModel(
                id=str(identifier),
                code=code,
                name=name,
                sort_order=sort_order,
                is_system=True,
                is_active=True,
            )
            for identifier, code, name, sort_order in SYSTEM_LOCATION_TYPES
        )
        session.commit()
    engine.dispose()
    app = create_app(test_settings)
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as test_client:
            yield test_client
