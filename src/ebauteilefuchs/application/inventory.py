"""M3 inventory service: immutable journal plus transactional materialized balances."""

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
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
from ebauteilefuchs.domain.locations import UNASSIGNED_LOCATION_ID


class ArchiveAction(StrEnum):
    KEEP_UNASSIGNED = "keep_unassigned"
    ASSIGN = "assign"
    DELETE_ARTICLE = "delete_article"


@dataclass(frozen=True, slots=True)
class ArchiveResolution:
    article_id: UUID
    action: ArchiveAction
    target_location_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ArchivePreview:
    location_ids: tuple[UUID, ...]
    positions: tuple[StockPosition, ...]


@dataclass(frozen=True, slots=True)
class ArchiveResult:
    booking: BookingResult
    archived_location_ids: tuple[UUID, ...]
    deactivated_article_ids: tuple[UUID, ...]


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

    def preview_location_archive(self, location_ids: list[UUID]) -> ArchivePreview:
        with self._uow_factory() as uow:
            subtree = self._archive_subtree(
                uow.inventory.list_locations(), location_ids
            )
            positions = tuple(
                item
                for item in uow.inventory.list_positions()
                if item.balance.location_id in subtree
            )
        return ArchivePreview(tuple(sorted(subtree, key=str)), positions)

    def archive_locations(
        self,
        *,
        location_ids: list[UUID],
        resolutions: list[ArchiveResolution],
        idempotency_key: str,
    ) -> ArchiveResult:
        key = clean_idempotency_key(idempotency_key)
        resolution_map = {item.article_id: item for item in resolutions}
        if len(resolution_map) != len(resolutions):
            raise ValidationError(
                "Für jeden Artikel ist genau eine Auswahl erforderlich."
            )
        payload = {
            "locations": sorted(str(item) for item in set(location_ids)),
            "resolutions": sorted(
                (
                    str(item.article_id),
                    item.action.value,
                    str(item.target_location_id) if item.target_location_id else None,
                )
                for item in resolutions
            ),
        }
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        with self._uow_factory() as uow:
            uow.begin_write()
            repeated = self._repeated(uow, key, fingerprint)
            if repeated:
                return ArchiveResult(repeated, tuple(), tuple())
            locations = uow.inventory.list_locations()
            by_id = {location.id: location for location in locations}
            subtree = self._archive_subtree(locations, location_ids)
            all_positions = uow.inventory.list_positions()
            positions = [
                item for item in all_positions if item.balance.location_id in subtree
            ]
            article_ids = {item.balance.article_id for item in positions}
            if set(resolution_map) != article_ids:
                raise ValidationError(
                    "Triff für jeden betroffenen Artikel genau eine Entscheidung."
                )
            unassigned = by_id.get(UNASSIGNED_LOCATION_ID)
            if unassigned is None or not unassigned.is_active:
                raise LocationNotFoundError(
                    "Der interne Lagerplatz ‚Ohne Lagerplatz‘ fehlt. "
                    "Führe die Migrationen aus."
                )
            changes: dict[tuple[UUID, UUID, str], Decimal] = {}
            deactivate_articles: set[UUID] = set()
            for position in positions:
                balance = position.balance
                resolution = resolution_map[balance.article_id]
                source_key = (balance.article_id, balance.location_id, balance.unit)
                changes[source_key] = (
                    changes.get(source_key, Decimal("0")) - balance.quantity
                )
                if resolution.action == ArchiveAction.KEEP_UNASSIGNED:
                    target_id = UNASSIGNED_LOCATION_ID
                elif resolution.action == ArchiveAction.ASSIGN:
                    target_id = resolution.target_location_id
                    target = by_id.get(target_id) if target_id else None
                    if target is None or not target.is_active or target_id in subtree:
                        raise ValidationError(
                            "Der neue Lagerplatz muss aktiv und außerhalb der Auswahl sein."
                        )
                else:
                    target_id = None
                    deactivate_articles.add(balance.article_id)
                if target_id is not None:
                    target_key = (balance.article_id, target_id, balance.unit)
                    changes[target_key] = (
                        changes.get(target_key, Decimal("0")) + balance.quantity
                    )

            for position in all_positions:
                balance = position.balance
                if (
                    balance.article_id in deactivate_articles
                    and balance.location_id not in subtree
                ):
                    key_to_zero = (
                        balance.article_id,
                        balance.location_id,
                        balance.unit,
                    )
                    changes[key_to_zero] = (
                        changes.get(key_to_zero, Decimal("0")) - balance.quantity
                    )

            now = datetime.now(UTC)
            transaction = InventoryTransaction(
                id=uuid4(),
                transaction_type=TransactionType.ADJUSTMENT,
                idempotency_key=key,
                request_fingerprint=fingerprint,
                comment="Lagerplätze revisionssicher archiviert",
                created_at=now,
            )
            uow.inventory.add_transaction(transaction)
            movements: list[InventoryMovement] = []
            for (article_id, location_id, unit), delta in changes.items():
                if delta == 0:
                    continue
                current = uow.inventory.get_balance(article_id, location_id, unit)
                old_quantity = current.quantity if current else Decimal("0")
                new_quantity = old_quantity + delta
                if new_quantity < 0:
                    raise InventoryConflictError(
                        "Ein Bestand wurde zwischenzeitlich verändert. Bitte erneut prüfen."
                    )
                if current:
                    balance = replace(
                        current,
                        quantity=new_quantity,
                        updated_at=now,
                        version=current.version + 1,
                    )
                    if not uow.inventory.update_balance(
                        balance, expected_version=current.version
                    ):
                        raise InventoryConflictError(
                            "Ein Bestand wurde zwischenzeitlich verändert. Bitte erneut prüfen."
                        )
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
                    uow.inventory.add_balance(balance)
                movement = InventoryMovement(
                    id=uuid4(),
                    transaction_id=transaction.id,
                    article_id=article_id,
                    location_id=location_id,
                    quantity_delta=delta,
                    unit=unit,
                    balance_after=new_quantity,
                    created_at=now,
                )
                uow.inventory.add_movement(movement)
                movements.append(movement)
            for article_id in deactivate_articles:
                article = uow.inventory.get_article(article_id)
                if article is not None:
                    uow.inventory.update_article(
                        replace(article, is_active=False, updated_at=now)
                    )
            for location_id in subtree:
                uow.inventory.update_location(
                    replace(by_id[location_id], is_active=False, updated_at=now)
                )
            uow.commit()
            return ArchiveResult(
                BookingResult(transaction=transaction, movements=tuple(movements)),
                tuple(sorted(subtree, key=str)),
                tuple(sorted(deactivate_articles, key=str)),
            )

    @staticmethod
    def _archive_subtree(locations: list, location_ids: list[UUID]) -> set[UUID]:
        roots = set(location_ids)
        if not roots:
            raise ValidationError("Wähle mindestens einen Lagerplatz aus.")
        if len(roots) > 500:
            raise ValidationError(
                "Es können höchstens 500 Lagerplätze archiviert werden."
            )
        if UNASSIGNED_LOCATION_ID in roots:
            raise ValidationError(
                "Der interne Lagerplatz kann nicht archiviert werden."
            )
        by_id = {location.id: location for location in locations}
        if roots - by_id.keys():
            raise LocationNotFoundError(
                "Mindestens ein Lagerplatz wurde nicht gefunden."
            )
        children: dict[UUID, list[UUID]] = {}
        for location in locations:
            if location.parent_id is not None:
                children.setdefault(location.parent_id, []).append(location.id)
        subtree = set(roots)
        pending = list(roots)
        while pending:
            for child_id in children.get(pending.pop(), []):
                if child_id not in subtree:
                    subtree.add(child_id)
                    pending.append(child_id)
        return subtree

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
