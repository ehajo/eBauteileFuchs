"""SQLAlchemy implementation of the generic, bounded supplier cache."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from ebauteilefuchs.application.ports.supplier_cache import SupplierCacheEntry
from ebauteilefuchs.persistence.models import SupplierCacheEntryModel


class SqlAlchemySupplierCache:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get(
        self,
        supplier_id: UUID,
        query_type: str,
        query_normalized: str,
        adapter_version: str,
        *,
        now: datetime,
    ) -> SupplierCacheEntry | None:
        with self._session_factory() as session:
            statement = select(SupplierCacheEntryModel).where(
                SupplierCacheEntryModel.supplier_id == str(supplier_id),
                SupplierCacheEntryModel.query_type == query_type,
                SupplierCacheEntryModel.query_normalized == query_normalized,
                SupplierCacheEntryModel.adapter_version == adapter_version,
                SupplierCacheEntryModel.expires_at > now,
            )
            model = session.scalar(statement)
            return _entry(model) if model else None

    def put(self, entry: SupplierCacheEntry) -> None:
        with self._session_factory() as session:
            session.execute(
                delete(SupplierCacheEntryModel).where(
                    SupplierCacheEntryModel.supplier_id == str(entry.supplier_id),
                    SupplierCacheEntryModel.query_type == entry.query_type,
                    SupplierCacheEntryModel.query_normalized == entry.query_normalized,
                    SupplierCacheEntryModel.adapter_version == entry.adapter_version,
                )
            )
            session.add(
                SupplierCacheEntryModel(
                    id=str(uuid4()),
                    supplier_id=str(entry.supplier_id),
                    query_type=entry.query_type,
                    query_normalized=entry.query_normalized,
                    adapter_version=entry.adapter_version,
                    response_json=entry.response_json,
                    status=entry.status,
                    created_at=entry.created_at,
                    expires_at=entry.expires_at,
                )
            )
            session.commit()

    def clear(self, supplier_id: UUID | None = None) -> int:
        with self._session_factory() as session:
            statement = delete(SupplierCacheEntryModel)
            if supplier_id:
                statement = statement.where(
                    SupplierCacheEntryModel.supplier_id == str(supplier_id)
                )
            result = session.execute(statement)
            session.commit()
            return result.rowcount or 0


def _entry(model: SupplierCacheEntryModel) -> SupplierCacheEntry:
    def aware(value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)

    return SupplierCacheEntry(
        supplier_id=UUID(model.supplier_id),
        query_type=model.query_type,
        query_normalized=model.query_normalized,
        adapter_version=model.adapter_version,
        response_json=model.response_json,
        status=model.status,
        created_at=aware(model.created_at),
        expires_at=aware(model.expires_at),
    )
