from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from ebauteilefuchs.config import Settings
from ebauteilefuchs.main import create_app
from ebauteilefuchs.persistence.article_catalog import (
    ATTRIBUTE_DEFINITIONS,
    ATTRIBUTE_IDS,
    CATEGORIES,
    CATEGORY_ATTRIBUTE_CODES,
    MOUSER_SUPPLIER,
)
from ebauteilefuchs.persistence.database import Base, create_database_engine
from ebauteilefuchs.persistence.location_types import SYSTEM_LOCATION_TYPES
from ebauteilefuchs.persistence.models import (
    AttributeDefinitionModel,
    CategoryAttributeModel,
    CategoryModel,
    LocationModel,
    LocationTypeModel,
    SupplierModel,
)


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        app_env="test",
        data_dir=tmp_path,
        database_url=f"sqlite+pysqlite:///{(tmp_path / 'test.db').as_posix()}",
        log_level="WARNING",
        mouser_api_key=None,
        public_base_url=None,
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
        session.flush()
        now = datetime.now(UTC)
        session.add(
            LocationModel(
                id="10000000-0000-4000-8000-000000000099",
                code="OHNE-LAGERPLATZ",
                normalized_code="ohne-lagerplatz",
                name="Ohne Lagerplatz",
                location_type_id="10000000-0000-4000-8000-000000000008",
                parent_id=None,
                parent_scope="__root__",
                description="Interner Sammelplatz für archivierte Lagerbereiche.",
                is_active=True,
                qr_token="internal-unassigned-v1",
                created_at=now,
                updated_at=now,
            )
        )
        category_ids = {code: identifier for identifier, code, *_ in CATEGORIES}
        session.add_all(
            CategoryModel(
                id=str(identifier),
                code=code,
                name=name,
                description=None,
                is_system=True,
                is_active=True,
                sort_order=sort_order,
            )
            for identifier, code, name, sort_order in CATEGORIES
        )
        session.add_all(
            AttributeDefinitionModel(
                id=str(ATTRIBUTE_IDS[code]),
                code=code,
                name=name,
                value_kind=value_kind,
                canonical_unit=unit,
                is_system=True,
                is_active=True,
            )
            for code, name, value_kind, unit in ATTRIBUTE_DEFINITIONS
        )
        session.flush()
        session.add_all(
            CategoryAttributeModel(
                category_id=str(category_ids[category_code]),
                attribute_definition_id=str(ATTRIBUTE_IDS[attribute_code]),
                sort_order=sort_order,
                is_typical=True,
                allowed_units_json="[]",
            )
            for category_code, attribute_codes in CATEGORY_ATTRIBUTE_CODES.items()
            for sort_order, attribute_code in enumerate(attribute_codes, start=10)
        )
        supplier_id, supplier_code, supplier_name, adapter_name = MOUSER_SUPPLIER
        session.add(
            SupplierModel(
                id=str(supplier_id),
                code=supplier_code,
                name=supplier_name,
                adapter_name=adapter_name,
                is_system=True,
                is_active=True,
            )
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
