"""SQLite-safe repository and unit of work for the M3 inventory journal."""

from datetime import UTC, datetime
from decimal import Decimal
from types import TracebackType
from uuid import UUID

from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from ebauteilefuchs.domain.articles import Article
from ebauteilefuchs.domain.errors import (
    IdempotencyConflictError,
    InventoryConflictError,
)
from ebauteilefuchs.domain.inventory import (
    InventoryBalance,
    InventoryMovement,
    InventoryTransaction,
    MovementDetails,
    StockPosition,
    TransactionType,
)
from ebauteilefuchs.domain.locations import Location
from ebauteilefuchs.persistence.articles import _article
from ebauteilefuchs.persistence.locations import _to_location
from ebauteilefuchs.persistence.models import (
    ArticleModel,
    InventoryBalanceModel,
    InventoryMovementModel,
    InventoryTransactionModel,
    LocationModel,
)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _decimal(value: Decimal) -> Decimal:
    return (
        value.quantize(Decimal("1"))
        if value == value.to_integral()
        else value.normalize()
    )


def _balance(model: InventoryBalanceModel) -> InventoryBalance:
    return InventoryBalance(
        id=UUID(model.id),
        article_id=UUID(model.article_id),
        location_id=UUID(model.location_id),
        quantity=_decimal(model.quantity),
        unit=model.unit,
        updated_at=_aware(model.updated_at),
        version=model.version,
    )


def _transaction(model: InventoryTransactionModel) -> InventoryTransaction:
    return InventoryTransaction(
        id=UUID(model.id),
        transaction_type=TransactionType(model.transaction_type),
        idempotency_key=model.idempotency_key,
        request_fingerprint=model.request_fingerprint,
        comment=model.comment,
        created_at=_aware(model.created_at),
    )


def _movement(model: InventoryMovementModel) -> InventoryMovement:
    return InventoryMovement(
        id=UUID(model.id),
        transaction_id=UUID(model.transaction_id),
        article_id=UUID(model.article_id),
        location_id=UUID(model.location_id),
        quantity_delta=_decimal(model.quantity_delta),
        unit=model.unit,
        balance_after=_decimal(model.balance_after),
        created_at=_aware(model.created_at),
    )


class SqlAlchemyInventoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_article(self, article_id: UUID) -> Article | None:
        model = self._session.get(ArticleModel, str(article_id))
        return _article(model) if model else None

    def get_location(self, location_id: UUID) -> Location | None:
        model = self._session.get(LocationModel, str(location_id))
        return _to_location(model) if model else None

    def get_balance(
        self, article_id: UUID, location_id: UUID, unit: str
    ) -> InventoryBalance | None:
        model = self._session.scalar(
            select(InventoryBalanceModel).where(
                InventoryBalanceModel.article_id == str(article_id),
                InventoryBalanceModel.location_id == str(location_id),
                InventoryBalanceModel.unit == unit,
            )
        )
        return _balance(model) if model else None

    def add_balance(self, balance: InventoryBalance) -> None:
        self._session.add(
            InventoryBalanceModel(
                id=str(balance.id),
                article_id=str(balance.article_id),
                location_id=str(balance.location_id),
                quantity=balance.quantity,
                unit=balance.unit,
                updated_at=balance.updated_at,
                version=balance.version,
            )
        )

    def update_balance(
        self, balance: InventoryBalance, *, expected_version: int
    ) -> bool:
        result = self._session.execute(
            update(InventoryBalanceModel)
            .where(
                InventoryBalanceModel.id == str(balance.id),
                InventoryBalanceModel.version == expected_version,
            )
            .values(
                quantity=balance.quantity,
                updated_at=balance.updated_at,
                version=balance.version,
            )
        )
        return result.rowcount == 1

    def has_movements(self, article_id: UUID, location_id: UUID, unit: str) -> bool:
        return bool(
            self._session.scalar(
                select(func.count(InventoryMovementModel.id)).where(
                    InventoryMovementModel.article_id == str(article_id),
                    InventoryMovementModel.location_id == str(location_id),
                    InventoryMovementModel.unit == unit,
                )
            )
        )

    def get_transaction_by_key(
        self, idempotency_key: str
    ) -> InventoryTransaction | None:
        model = self._session.scalar(
            select(InventoryTransactionModel).where(
                InventoryTransactionModel.idempotency_key == idempotency_key
            )
        )
        return _transaction(model) if model else None

    def add_transaction(self, transaction: InventoryTransaction) -> None:
        self._session.add(
            InventoryTransactionModel(
                id=str(transaction.id),
                transaction_type=transaction.transaction_type.value,
                idempotency_key=transaction.idempotency_key,
                request_fingerprint=transaction.request_fingerprint,
                comment=transaction.comment,
                created_at=transaction.created_at,
            )
        )
        self._session.flush()

    def add_movement(self, movement: InventoryMovement) -> None:
        self._session.add(
            InventoryMovementModel(
                id=str(movement.id),
                transaction_id=str(movement.transaction_id),
                article_id=str(movement.article_id),
                location_id=str(movement.location_id),
                quantity_delta=movement.quantity_delta,
                unit=movement.unit,
                balance_after=movement.balance_after,
                created_at=movement.created_at,
            )
        )

    def list_transaction_movements(
        self, transaction_id: UUID
    ) -> list[InventoryMovement]:
        statement = (
            select(InventoryMovementModel)
            .where(InventoryMovementModel.transaction_id == str(transaction_id))
            .order_by(InventoryMovementModel.created_at, InventoryMovementModel.id)
        )
        return [_movement(item) for item in self._session.scalars(statement).all()]

    def _location_paths(self) -> dict[str, str]:
        locations = self._session.scalars(select(LocationModel)).all()
        by_id = {item.id: item for item in locations}
        cache: dict[str, str] = {}

        def path(model: LocationModel) -> str:
            if model.id in cache:
                return cache[model.id]
            parts = [model.code]
            parent_id = model.parent_id
            seen = {model.id}
            while parent_id and parent_id not in seen:
                seen.add(parent_id)
                parent = by_id.get(parent_id)
                if parent is None:
                    break
                parts.append(parent.code)
                parent_id = parent.parent_id
            cache[model.id] = " / ".join(reversed(parts))
            return cache[model.id]

        return {item.id: path(item) for item in locations}

    def list_positions(
        self,
        *,
        article_id: UUID | None = None,
        location_id: UUID | None = None,
        include_zero: bool = False,
    ) -> list[StockPosition]:
        statement = (
            select(InventoryBalanceModel, ArticleModel, LocationModel)
            .join(ArticleModel, ArticleModel.id == InventoryBalanceModel.article_id)
            .join(LocationModel, LocationModel.id == InventoryBalanceModel.location_id)
        )
        if article_id:
            statement = statement.where(
                InventoryBalanceModel.article_id == str(article_id)
            )
        if location_id:
            statement = statement.where(
                InventoryBalanceModel.location_id == str(location_id)
            )
        if not include_zero:
            statement = statement.where(InventoryBalanceModel.quantity > 0)
        statement = statement.order_by(ArticleModel.name, LocationModel.code)
        paths = self._location_paths()
        return [
            StockPosition(
                balance=_balance(balance_model),
                article_name=article_model.name,
                location_code=location_model.code,
                location_name=location_model.name,
                location_path=paths.get(location_model.id, location_model.code),
            )
            for balance_model, article_model, location_model in self._session.execute(
                statement
            ).all()
        ]

    def list_movements(
        self,
        *,
        article_id: UUID | None = None,
        location_id: UUID | None = None,
        limit: int = 25,
    ) -> list[MovementDetails]:
        statement = (
            select(
                InventoryMovementModel,
                InventoryTransactionModel,
                ArticleModel,
                LocationModel,
            )
            .join(
                InventoryTransactionModel,
                InventoryTransactionModel.id == InventoryMovementModel.transaction_id,
            )
            .join(ArticleModel, ArticleModel.id == InventoryMovementModel.article_id)
            .join(LocationModel, LocationModel.id == InventoryMovementModel.location_id)
        )
        if article_id:
            statement = statement.where(
                InventoryMovementModel.article_id == str(article_id)
            )
        if location_id:
            statement = statement.where(
                InventoryMovementModel.location_id == str(location_id)
            )
        statement = statement.order_by(
            InventoryMovementModel.created_at.desc(),
            InventoryMovementModel.id.desc(),
        ).limit(max(1, min(limit, 250)))
        paths = self._location_paths()
        return [
            MovementDetails(
                movement=_movement(movement_model),
                transaction_type=TransactionType(transaction_model.transaction_type),
                transaction_comment=transaction_model.comment,
                article_name=article_model.name,
                location_code=location_model.code,
                location_path=paths.get(location_model.id, location_model.code),
            )
            for (
                movement_model,
                transaction_model,
                article_model,
                location_model,
            ) in self._session.execute(statement).all()
        ]


class SqlAlchemyInventoryUnitOfWork:
    """Serialize SQLite writers with BEGIN IMMEDIATE before reading balances."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self.inventory: SqlAlchemyInventoryRepository

    def __enter__(self) -> "SqlAlchemyInventoryUnitOfWork":
        self._session = self._session_factory()
        self.inventory = SqlAlchemyInventoryRepository(self._session)
        return self

    def begin_write(self) -> None:
        if self._session is None:
            raise RuntimeError("Die Unit of Work wurde nicht geöffnet.")
        try:
            self._session.execute(text("BEGIN IMMEDIATE"))
        except OperationalError as error:
            self._session.close()
            self._session = None
            raise InventoryConflictError(
                "Der Bestand wird gerade geändert. Bitte versuche die Buchung erneut."
            ) from error

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
            if "idempotency" in str(error).casefold():
                raise IdempotencyConflictError(
                    "Dieser Buchungsschlüssel wurde bereits verwendet."
                ) from error
            raise InventoryConflictError(
                "Die Buchung kollidiert mit einer gleichzeitigen Änderung."
            ) from error
        except OperationalError as error:
            self._session.rollback()
            raise InventoryConflictError(
                "Der Bestand wird gerade geändert. Bitte versuche die Buchung erneut."
            ) from error
