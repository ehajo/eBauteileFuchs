"""M5 global local-first AND search across catalog and inventory data."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from ebauteilefuchs.application.articles import ArticleDetails, ArticleService
from ebauteilefuchs.application.inventory import InventoryService
from ebauteilefuchs.application.locations import LocationDetails, LocationService
from ebauteilefuchs.domain.articles import normalize_part_number, normalize_search_text
from ebauteilefuchs.domain.errors import ValidationError
from ebauteilefuchs.domain.inventory import StockPosition


@dataclass(frozen=True, slots=True)
class GlobalSearchItem:
    details: ArticleDetails
    positions: tuple[StockPosition, ...]
    totals: dict[str, Decimal]


@dataclass(frozen=True, slots=True)
class GlobalSearchResult:
    query: str
    tokens: tuple[str, ...]
    items: tuple[GlobalSearchItem, ...]


class GlobalSearchService:
    def __init__(
        self,
        articles: ArticleService,
        inventory: InventoryService,
        locations: LocationService,
    ) -> None:
        self._articles = articles
        self._inventory = inventory
        self._locations = locations

    def search(
        self,
        query: str,
        *,
        category_id: UUID | None = None,
        with_stock: bool = False,
        location_scope_id: UUID | None = None,
    ) -> GlobalSearchResult:
        cleaned = " ".join(query.split())
        if len(cleaned) > 200:
            raise ValidationError("Die Suche darf höchstens 200 Zeichen enthalten.")
        tokens = tuple(normalize_search_text(cleaned).split())
        if cleaned and not tokens:
            raise ValidationError("Die Suche enthält keine verwendbaren Zeichen.")

        categories = self._articles.list_categories()
        if category_id and all(item.id != category_id for item in categories):
            raise ValidationError(
                "Die gewählte Kategorie ist nicht aktiv oder unbekannt."
            )

        location_details = self._locations.list_details(include_inactive=False)
        known_location_ids = {item.location.id for item in location_details}
        if location_scope_id and location_scope_id not in known_location_ids:
            raise ValidationError(
                "Der gewählte Lagerbereich ist nicht aktiv oder unbekannt."
            )
        scoped_ids = self._scoped_location_ids(location_details, location_scope_id)

        positions = self._inventory.list_positions()
        positions_by_article: dict[UUID, list[StockPosition]] = {}
        for position in positions:
            positions_by_article.setdefault(position.balance.article_id, []).append(
                position
            )

        items: list[GlobalSearchItem] = []
        for details in self._articles.list_articles(include_inactive=False):
            if category_id and details.category.id != category_id:
                continue
            article_positions = positions_by_article.get(details.article.id, [])
            if with_stock and not article_positions:
                continue
            if location_scope_id and not any(
                item.balance.location_id in scoped_ids for item in article_positions
            ):
                continue
            location_text = " ".join(
                f"{item.location_path} {item.location_code} {item.location_name}"
                for item in article_positions
            )
            haystack = normalize_search_text(
                f"{details.article.search_text} {location_text}"
            )
            compact_haystack = haystack.replace(" ", "")
            if tokens and not all(
                token in haystack or token in compact_haystack for token in tokens
            ):
                continue
            totals: dict[str, Decimal] = {}
            for position in article_positions:
                totals[position.balance.unit] = (
                    totals.get(position.balance.unit, Decimal("0"))
                    + position.balance.quantity
                )
            items.append(
                GlobalSearchItem(
                    details=details,
                    positions=tuple(
                        sorted(article_positions, key=lambda item: item.location_path)
                    ),
                    totals=totals,
                )
            )

        normalized_part = normalize_part_number(cleaned) if cleaned else ""
        items.sort(key=lambda item: self._rank(item, normalized_part, tokens))
        return GlobalSearchResult(cleaned, tokens, tuple(items[:250]))

    @staticmethod
    def _scoped_location_ids(
        details: list[LocationDetails], scope_id: UUID | None
    ) -> set[UUID]:
        if scope_id is None:
            return {item.location.id for item in details}
        return {
            item.location.id
            for item in details
            if any(part.id == scope_id for part in item.path)
        }

    @staticmethod
    def _rank(
        item: GlobalSearchItem, normalized_part: str, tokens: tuple[str, ...]
    ) -> tuple[int, str]:
        details = item.details
        identifiers = [
            details.article.normalized_manufacturer_part_number or "",
            *(part.normalized_supplier_part_number for part in details.supplier_parts),
        ]
        if normalized_part and normalized_part in identifiers:
            priority = 0
        elif tokens and normalize_search_text(details.article.name).startswith(
            tokens[0]
        ):
            priority = 1
        else:
            priority = 2
        return priority, details.article.name.casefold()
