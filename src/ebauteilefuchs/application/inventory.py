"""M3 inventory service: immutable journal plus transactional materialized balances."""

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from ebauteilefuchs.application.ports.inventory import InventoryUnitOfWorkFactory
from ebauteilefuchs.domain.errors import (
    ArticleNotFoundError,
    IdempotencyConflictError,
    InactiveLocationError,
    InsufficientStockError,
    InventoryConflictError,
    LocationNotFoundError,
    ValidationError,
)
from ebauteilefuchs.domain.inventory import (
    DEFAULT_UNIT,
    BookingResult,
    InventoryBalance,
    InventoryMovement,
    InventoryTransaction,
    MovementDetails,
    StockPosition,
    TransactionType,
    clean_idempotency_key,
    clean_unit,
    parse_quantity,
    positive_quantity,
)


class InventoryService:
    def __init__(self, uow_factory: InventoryUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def list_positions(
        self,
        *,
        article_id: UUID | None = None,
        location_id: UUID | None = None,
        include_zero: bool = False,
    ) -> list[StockPosition]:
        with self._uow_factory() as uow:
            return uow.inventory.list_positions(
                article_id=article_id,
                location_id=location_id,
                include_zero=include_zero,
            )

    def list_movements(
        self,
        *,
        article_id: UUID | None = None,
        location_id: UUID | None = None,
        limit: int = 25,
    ) -> list[MovementDetails]:
        with self._uow_factory() as uow:
            return uow.inventory.list_movements(
                article_id=article_id, location_id=location_id, limit=limit
            )

    def totals(self, article_id: UUID) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = {}
        for item in self.list_positions(article_id=article_id):
            totals[item.balance.unit] = (
                totals.get(item.balance.unit, Decimal("0")) + item.balance.quantity
            )
        return totals

    def initial(
        self,
        *,
        article_id: UUID,
        location_id: UUID,
        quantity: Decimal | str | int,
        idempotency_key: str,
        unit: str = DEFAULT_UNIT,
        comment: str | None = None,
    ) -> BookingResult:
        parsed = positive_quantity(quantity)
        return self._single(
            transaction_type=TransactionType.INITIAL,
            article_id=article_id,
            location_id=location_id,
            delta=parsed,
            idempotency_key=idempotency_key,
            unit=unit,
            comment=comment,
            require_empty_history=True,
        )

    def stock_in(
        self,
        *,
        article_id: UUID,
        location_id: UUID,
        quantity: Decimal | str | int,
        idempotency_key: str,
        unit: str = DEFAULT_UNIT,
        comment: str | None = None,
    ) -> BookingResult:
        return self._single(
            transaction_type=TransactionType.STOCK_IN,
            article_id=article_id,
            location_id=location_id,
            delta=positive_quantity(quantity),
            idempotency_key=idempotency_key,
            unit=unit,
            comment=comment,
        )

    def stock_out(
        self,
        *,
        article_id: UUID,
        location_id: UUID,
        quantity: Decimal | str | int,
        idempotency_key: str,
        unit: str = DEFAULT_UNIT,
        comment: str | None = None,
    ) -> BookingResult:
        return self._single(
            transaction_type=TransactionType.STOCK_OUT,
            article_id=article_id,
            location_id=location_id,
            delta=-positive_quantity(quantity),
            idempotency_key=idempotency_key,
            unit=unit,
            comment=comment,
        )

    def adjust(
        self,
        *,
        article_id: UUID,
        location_id: UUID,
        idempotency_key: str,
        unit: str = DEFAULT_UNIT,
        difference: Decimal | str | int | None = None,
        target_quantity: Decimal | str | int | None = None,
        comment: str | None = None,
    ) -> BookingResult:
        if (difference is None) == (target_quantity is None):
            raise ValidationError(
                "Gib entweder eine Differenz oder einen gezählten Zielbestand an."
            )
        parsed_unit = clean_unit(unit)
        key = clean_idempotency_key(idempotency_key)
        clean_comment = self._comment(comment)
        target = (
            parse_quantity(target_quantity, "Zielbestand")
            if target_quantity is not None
            else None
        )
        if target is not None and target < 0:
            raise ValidationError("Der Zielbestand darf nicht negativ sein.")
        parsed_difference = (
            parse_quantity(difference, "Korrekturdifferenz")
            if difference is not None
            else None
        )
        fingerprint = self._fingerprint(
            TransactionType.ADJUSTMENT,
            article_id,
            location_id,
            parsed_difference,
            parsed_unit,
            clean_comment,
            target=target,
        )
        with self._uow_factory() as uow:
            uow.begin_write()
            repeated = self._repeated(uow, key, fingerprint)
            if repeated:
                return repeated
            self._require_references(uow, article_id, location_id)
            current = uow.inventory.get_balance(article_id, location_id, parsed_unit)
            old_quantity = current.quantity if current else Decimal("0")
            delta = target - old_quantity if target is not None else parsed_difference
            assert delta is not None
            if delta == 0:
                raise ValidationError("Die Korrektur verändert den Bestand nicht.")
            return self._write(
                uow,
                TransactionType.ADJUSTMENT,
                key,
                fingerprint,
                clean_comment,
                [(article_id, location_id, delta, parsed_unit, current)],
            )

    def transfer(
        self,
        *,
        article_id: UUID,
        source_location_id: UUID,
        target_location_id: UUID,
        quantity: Decimal | str | int,
        idempotency_key: str,
        unit: str = DEFAULT_UNIT,
        comment: str | None = None,
    ) -> BookingResult:
        if source_location_id == target_location_id:
            raise ValidationError("Quelle und Ziel müssen verschieden sein.")
        parsed = positive_quantity(quantity)
        parsed_unit = clean_unit(unit)
        key = clean_idempotency_key(idempotency_key)
        clean_comment = self._comment(comment)
        fingerprint = self._fingerprint(
            TransactionType.TRANSFER,
            article_id,
            source_location_id,
            parsed,
            parsed_unit,
            clean_comment,
            target_location_id=target_location_id,
        )
        with self._uow_factory() as uow:
            uow.begin_write()
            repeated = self._repeated(uow, key, fingerprint)
            if repeated:
                return repeated
            self._require_references(uow, article_id, source_location_id)
            self._require_references(uow, article_id, target_location_id)
            source = uow.inventory.get_balance(
                article_id, source_location_id, parsed_unit
            )
            target = uow.inventory.get_balance(
                article_id, target_location_id, parsed_unit
            )
            return self._write(
                uow,
                TransactionType.TRANSFER,
                key,
                fingerprint,
                clean_comment,
                [
                    (article_id, source_location_id, -parsed, parsed_unit, source),
                    (article_id, target_location_id, parsed, parsed_unit, target),
                ],
            )

    def _single(
        self,
        *,
        transaction_type: TransactionType,
        article_id: UUID,
        location_id: UUID,
        delta: Decimal,
        idempotency_key: str,
        unit: str,
        comment: str | None,
        require_empty_history: bool = False,
    ) -> BookingResult:
        parsed_unit = clean_unit(unit)
        key = clean_idempotency_key(idempotency_key)
        clean_comment = self._comment(comment)
        fingerprint = self._fingerprint(
            transaction_type,
            article_id,
            location_id,
            delta,
            parsed_unit,
            clean_comment,
        )
        with self._uow_factory() as uow:
            uow.begin_write()
            repeated = self._repeated(uow, key, fingerprint)
            if repeated:
                return repeated
            self._require_references(uow, article_id, location_id)
            current = uow.inventory.get_balance(article_id, location_id, parsed_unit)
            if require_empty_history and uow.inventory.has_movements(
                article_id, location_id, parsed_unit
            ):
                raise InventoryConflictError(
                    "Für diesen Artikel und Lagerplatz existiert bereits eine Historie. "
                    "Verwende eine Bestandskorrektur."
                )
            return self._write(
                uow,
                transaction_type,
                key,
                fingerprint,
                clean_comment,
                [(article_id, location_id, delta, parsed_unit, current)],
            )

    def _write(self, uow, transaction_type, key, fingerprint, comment, changes):
        now = datetime.now(UTC)
        transaction = InventoryTransaction(
            id=uuid4(),
            transaction_type=transaction_type,
            idempotency_key=key,
            request_fingerprint=fingerprint,
            comment=comment,
            created_at=now,
        )
        prepared: list[tuple[InventoryBalance, int | None, Decimal]] = []
        for article_id, location_id, delta, unit, current in changes:
            old_quantity = current.quantity if current else Decimal("0")
            new_quantity = old_quantity + delta
            if new_quantity < 0:
                raise InsufficientStockError(
                    "Der vorhandene Bestand reicht für diese Buchung nicht aus.",
                    available=str(old_quantity),
                )
            if current:
                balance = replace(
                    current,
                    quantity=new_quantity,
                    updated_at=now,
                    version=current.version + 1,
                )
                expected_version: int | None = current.version
            else:
                balance = InventoryBalance(
                    id=uuid4(),
                    article_id=article_id,
                    location_id=location_id,
                    quantity=new_quantity,
                    unit=unit,
                    updated_at=now,
                    version=1,
                )
                expected_version = None
            prepared.append((balance, expected_version, delta))

        uow.inventory.add_transaction(transaction)
        movements: list[InventoryMovement] = []
        for balance, expected_version, delta in prepared:
            if expected_version is None:
                uow.inventory.add_balance(balance)
            elif not uow.inventory.update_balance(
                balance, expected_version=expected_version
            ):
                raise InventoryConflictError(
                    "Der Bestand hat sich zwischenzeitlich geändert. Bitte neu prüfen."
                )
            movement = InventoryMovement(
                id=uuid4(),
                transaction_id=transaction.id,
                article_id=balance.article_id,
                location_id=balance.location_id,
                quantity_delta=delta,
                unit=balance.unit,
                balance_after=balance.quantity,
                created_at=now,
            )
            uow.inventory.add_movement(movement)
            movements.append(movement)
        uow.commit()
        return BookingResult(transaction=transaction, movements=tuple(movements))

    @staticmethod
    def _require_references(uow, article_id: UUID, location_id: UUID) -> None:
        article = uow.inventory.get_article(article_id)
        if article is None or not article.is_active:
            raise ArticleNotFoundError("Der Artikel ist nicht aktiv oder unbekannt.")
        location = uow.inventory.get_location(location_id)
        if location is None:
            raise LocationNotFoundError("Der Lagerplatz wurde nicht gefunden.")
        if not location.is_active:
            raise InactiveLocationError("Der Lagerplatz ist deaktiviert.")

    @staticmethod
    def _repeated(uow, key: str, fingerprint: str) -> BookingResult | None:
        existing = uow.inventory.get_transaction_by_key(key)
        if existing is None:
            return None
        if existing.request_fingerprint != fingerprint:
            raise IdempotencyConflictError(
                "Dieser Buchungsschlüssel gehört bereits zu einem anderen Vorgang."
            )
        return BookingResult(
            transaction=existing,
            movements=tuple(uow.inventory.list_transaction_movements(existing.id)),
            repeated=True,
        )

    @staticmethod
    def _comment(value: str | None) -> str | None:
        cleaned = " ".join((value or "").split()) or None
        if cleaned and len(cleaned) > 1_000:
            raise ValidationError(
                "Die Buchungsnotiz darf höchstens 1000 Zeichen haben."
            )
        return cleaned

    @staticmethod
    def _fingerprint(
        transaction_type: TransactionType,
        article_id: UUID,
        location_id: UUID,
        quantity: Decimal | None,
        unit: str,
        comment: str | None,
        **extra,
    ) -> str:
        values = {
            "type": transaction_type.value,
            "article_id": str(article_id),
            "location_id": str(location_id),
            "quantity": str(quantity) if quantity is not None else None,
            "unit": unit,
            "comment": comment,
            **{
                key: str(value) if value is not None else None
                for key, value in extra.items()
            },
        }
        serialized = json.dumps(values, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
