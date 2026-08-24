"""SQLAlchemy implementation of location repositories and unit of work."""

from datetime import UTC, datetime
from types import TracebackType
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from ebauteilefuchs.domain.errors import (
    DuplicateLocationCodeError,
    LocationInUseError,
)
from ebauteilefuchs.domain.locations import Location, LocationType
from ebauteilefuchs.persistence.models import LocationModel, LocationTypeModel

ROOT_SCOPE = "__root__"


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _to_type(model: LocationTypeModel) -> LocationType:
    return LocationType(
        id=UUID(model.id),
        code=model.code,
        name=model.name,
        sort_order=model.sort_order,
        is_system=model.is_system,
        is_active=model.is_active,
    )


def _to_location(model: LocationModel) -> Location:
    return Location(
        id=UUID(model.id),
        code=model.code,
        normalized_code=model.normalized_code,
        name=model.name,
        location_type_id=UUID(model.location_type_id),
        parent_id=UUID(model.parent_id) if model.parent_id else None,
        description=model.description,
        is_active=model.is_active,
        qr_token=model.qr_token,
        created_at=_aware(model.created_at),
        updated_at=_aware(model.updated_at),
    )


class SqlAlchemyLocationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_types(self, *, include_inactive: bool = False) -> list[LocationType]:
        statement = select(LocationTypeModel)
        if not include_inactive:
            statement = statement.where(LocationTypeModel.is_active.is_(True))
        statement = statement.order_by(
            LocationTypeModel.sort_order, LocationTypeModel.name
        )
        return [_to_type(model) for model in self._session.scalars(statement).all()]

    def get_type(self, location_type_id: UUID) -> LocationType | None:
        model = self._session.get(LocationTypeModel, str(location_type_id))
        return _to_type(model) if model else None

    def get_type_by_code(self, code: str) -> LocationType | None:
        model = self._session.scalar(
            select(LocationTypeModel).where(LocationTypeModel.code == code)
        )
        return _to_type(model) if model else None

    def add_type(self, location_type: LocationType) -> None:
        self._session.add(
            LocationTypeModel(
                id=str(location_type.id),
                code=location_type.code,
                name=location_type.name,
                sort_order=location_type.sort_order,
                is_system=location_type.is_system,
                is_active=location_type.is_active,
            )
        )

    def update_type(self, location_type: LocationType) -> None:
        model = self._session.get(LocationTypeModel, str(location_type.id))
        if model is None:
            return
        model.code = location_type.code
        model.name = location_type.name
        model.sort_order = location_type.sort_order
        model.is_active = location_type.is_active

    def list_locations(self, *, include_inactive: bool = True) -> list[Location]:
        statement = select(LocationModel)
        if not include_inactive:
            statement = statement.where(LocationModel.is_active.is_(True))
        statement = statement.order_by(
            LocationModel.parent_scope,
            LocationModel.normalized_code,
            LocationModel.name,
        )
        return [_to_location(model) for model in self._session.scalars(statement).all()]

    def get(self, location_id: UUID) -> Location | None:
        model = self._session.get(LocationModel, str(location_id))
        return _to_location(model) if model else None

    def get_by_qr_token(self, qr_token: str) -> Location | None:
        model = self._session.scalar(
            select(LocationModel).where(LocationModel.qr_token == qr_token)
        )
        return _to_location(model) if model else None

    def find_sibling(
        self,
        parent_id: UUID | None,
        normalized_code: str,
        *,
        exclude_id: UUID | None = None,
    ) -> Location | None:
        statement = select(LocationModel).where(
            LocationModel.parent_scope == (str(parent_id) if parent_id else ROOT_SCOPE),
            LocationModel.normalized_code == normalized_code,
        )
        if exclude_id is not None:
            statement = statement.where(LocationModel.id != str(exclude_id))
        model = self._session.scalar(statement)
        return _to_location(model) if model else None

    def list_children(
        self, parent_id: UUID, *, include_inactive: bool = True
    ) -> list[Location]:
        statement = select(LocationModel).where(
            LocationModel.parent_id == str(parent_id)
        )
        if not include_inactive:
            statement = statement.where(LocationModel.is_active.is_(True))
        statement = statement.order_by(
            LocationModel.normalized_code, LocationModel.name
        )
        return [_to_location(model) for model in self._session.scalars(statement).all()]

    def add(self, location: Location) -> None:
        self._session.add(
            LocationModel(
                id=str(location.id),
                code=location.code,
                normalized_code=location.normalized_code,
                name=location.name,
                location_type_id=str(location.location_type_id),
                parent_id=str(location.parent_id) if location.parent_id else None,
                parent_scope=str(location.parent_id)
                if location.parent_id
                else ROOT_SCOPE,
                description=location.description,
                is_active=location.is_active,
                qr_token=location.qr_token,
                created_at=location.created_at,
                updated_at=location.updated_at,
            )
        )

    def update(self, location: Location) -> None:
        model = self._session.get(LocationModel, str(location.id))
        if model is None:
            return
        model.code = location.code
        model.normalized_code = location.normalized_code
        model.name = location.name
        model.location_type_id = str(location.location_type_id)
        model.parent_id = str(location.parent_id) if location.parent_id else None
        model.parent_scope = (
            str(location.parent_id) if location.parent_id else ROOT_SCOPE
        )
        model.description = location.description
        model.is_active = location.is_active
        model.updated_at = location.updated_at

    def remove(self, location_id: UUID) -> None:
        model = self._session.get(LocationModel, str(location_id))
        if model is None:
            return
        self._session.delete(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            self._session.rollback()
            raise LocationInUseError(
                "Dieser Lagerplatz wird noch von Unterplätzen, Beständen oder "
                "Bestandsbewegungen verwendet und kann deshalb nur deaktiviert werden."
            ) from error


class SqlAlchemyLocationUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self.locations: SqlAlchemyLocationRepository

    def __enter__(self) -> "SqlAlchemyLocationUnitOfWork":
        self._session = self._session_factory()
        self.locations = SqlAlchemyLocationRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return
        if exc_type is not None:
            self._session.rollback()
        self._session.close()

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("Die Unit of Work wurde nicht geöffnet.")
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise DuplicateLocationCodeError(
                "Die Lagerplatzkennung oder der QR-Token ist bereits vorhanden."
            ) from error
