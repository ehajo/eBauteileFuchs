"""M2 application service for article catalog and duplicate prevention."""

import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from difflib import SequenceMatcher
from uuid import UUID, uuid4

from ebauteilefuchs.application.ports.articles import ArticleUnitOfWorkFactory
from ebauteilefuchs.domain.articles import (
    Article,
    ArticleAttribute,
    ArticleDraft,
    AttributeDefinition,
    AttributeInput,
    Category,
    CategoryAttribute,
    Manufacturer,
    Supplier,
    SupplierPart,
    SupplierPartInput,
    clean_text,
    normalize_manufacturer_name,
    normalize_part_number,
    normalize_search_text,
    normalized_numeric_value,
    validate_optional_url,
)
from ebauteilefuchs.domain.errors import (
    ArticleNotFoundError,
    DuplicateArticleError,
    DuplicateReferenceError,
    ReferenceNotFoundError,
    ValidationError,
)


@dataclass(frozen=True, slots=True)
class ArticleDetails:
    article: Article
    manufacturer: Manufacturer | None
    category: Category
    attributes: tuple[ArticleAttribute, ...]
    supplier_parts: tuple[SupplierPart, ...]


@dataclass(frozen=True, slots=True)
class DuplicateCandidate:
    article_id: UUID
    name: str
    match_level: int
    reason: str
    can_override: bool


class ArticleService:
    def __init__(self, uow_factory: ArticleUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def list_manufacturers(
        self, *, include_inactive: bool = False
    ) -> list[Manufacturer]:
        with self._uow_factory() as uow:
            return uow.articles.list_manufacturers(include_inactive=include_inactive)

    def create_manufacturer(self, name: str) -> Manufacturer:
        cleaned = clean_text(name, "Hersteller", 120, required=True)
        assert cleaned is not None
        normalized = normalize_manufacturer_name(cleaned)
        with self._uow_factory() as uow:
            if uow.articles.get_manufacturer_by_normalized(normalized):
                raise DuplicateReferenceError(
                    "Dieser Hersteller ist bereits vorhanden."
                )
            now = datetime.now(UTC)
            manufacturer = Manufacturer(
                id=uuid4(),
                name=cleaned,
                normalized_name=normalized,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            uow.articles.add_manufacturer(manufacturer)
            uow.commit()
            return manufacturer

    def update_manufacturer(
        self, manufacturer_id: UUID, *, name: str, is_active: bool
    ) -> Manufacturer:
        cleaned = clean_text(name, "Hersteller", 120, required=True)
        assert cleaned is not None
        normalized = normalize_manufacturer_name(cleaned)
        with self._uow_factory() as uow:
            current = uow.articles.get_manufacturer(manufacturer_id)
            if current is None:
                raise ReferenceNotFoundError("Der Hersteller wurde nicht gefunden.")
            duplicate = uow.articles.get_manufacturer_by_normalized(normalized)
            if duplicate and duplicate.id != manufacturer_id:
                raise DuplicateReferenceError(
                    "Dieser Hersteller ist bereits vorhanden."
                )
            updated = replace(
                current,
                name=cleaned,
                normalized_name=normalized,
                is_active=is_active,
                updated_at=datetime.now(UTC),
            )
            uow.articles.update_manufacturer(updated)
            uow.commit()
            return updated

    def list_categories(self, *, include_inactive: bool = False) -> list[Category]:
        with self._uow_factory() as uow:
            return uow.articles.list_categories(include_inactive=include_inactive)

    def create_category(
        self, *, code: str, name: str, description: str | None, sort_order: int = 100
    ) -> Category:
        cleaned_code = code.strip().casefold()
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,39}", cleaned_code):
            raise ValidationError(
                "Der Kategoriecode muss mit einem Buchstaben beginnen und darf nur "
                "Kleinbuchstaben, Ziffern und Unterstriche enthalten."
            )
        cleaned_name = clean_text(name, "Kategorie", 80, required=True)
        cleaned_description = clean_text(description, "Beschreibung", 1_000)
        assert cleaned_name is not None
        if not 0 <= sort_order <= 10_000:
            raise ValidationError("Die Sortierung muss zwischen 0 und 10000 liegen.")
        with self._uow_factory() as uow:
            if any(
                item.code == cleaned_code
                for item in uow.articles.list_categories(include_inactive=True)
            ):
                raise DuplicateReferenceError("Diese Kategorie ist bereits vorhanden.")
            category = Category(
                id=uuid4(),
                code=cleaned_code,
                name=cleaned_name,
                description=cleaned_description,
                is_system=False,
                is_active=True,
                sort_order=sort_order,
            )
            uow.articles.add_category(category)
            uow.commit()
            return category

    def update_category(
        self,
        category_id: UUID,
        *,
        name: str,
        description: str | None,
        sort_order: int,
        is_active: bool,
    ) -> Category:
        cleaned_name = clean_text(name, "Kategorie", 80, required=True)
        assert cleaned_name is not None
        if not 0 <= sort_order <= 10_000:
            raise ValidationError("Die Sortierung muss zwischen 0 und 10000 liegen.")
        with self._uow_factory() as uow:
            current = uow.articles.get_category(category_id)
            if current is None:
                raise ReferenceNotFoundError("Die Kategorie wurde nicht gefunden.")
            updated = replace(
                current,
                name=cleaned_name,
                description=clean_text(description, "Beschreibung", 1_000),
                sort_order=sort_order,
                is_active=is_active,
            )
            uow.articles.update_category(updated)
            uow.commit()
            return updated

    def list_category_attributes(self, category_id: UUID) -> list[CategoryAttribute]:
        with self._uow_factory() as uow:
            if uow.articles.get_category(category_id) is None:
                raise ReferenceNotFoundError("Die Kategorie wurde nicht gefunden.")
            return uow.articles.list_category_attributes(category_id)

    def list_suppliers(self) -> list[Supplier]:
        with self._uow_factory() as uow:
            return uow.articles.list_suppliers()

    def list_articles(
        self, *, query: str | None = None, include_inactive: bool = True
    ) -> list[ArticleDetails]:
        with self._uow_factory() as uow:
            if query:
                tokens = tuple(normalize_search_text(query).split())
                articles = uow.articles.search_articles(
                    tokens, include_inactive=include_inactive
                )
            else:
                articles = uow.articles.list_articles(include_inactive=include_inactive)
            return [self._details(uow, article) for article in articles]

    def get(self, article_id: UUID) -> ArticleDetails:
        with self._uow_factory() as uow:
            article = uow.articles.get_article(article_id)
            if article is None:
                raise ArticleNotFoundError("Der Artikel wurde nicht gefunden.")
            return self._details(uow, article)

    def check_duplicates(
        self, draft: ArticleDraft, *, exclude_article_id: UUID | None = None
    ) -> list[DuplicateCandidate]:
        cleaned = self._clean_draft(draft)
        with self._uow_factory() as uow:
            return self._duplicate_candidates(
                uow, cleaned, exclude_article_id=exclude_article_id
            )

    def create(self, draft: ArticleDraft) -> ArticleDetails:
        cleaned = self._clean_draft(draft)
        article_id = uuid4()
        with self._uow_factory() as uow:
            category = self._require_active_category(uow, cleaned.category_id)
            duplicates = self._duplicate_candidates(uow, cleaned)
            self._enforce_duplicates(duplicates, cleaned.acknowledge_similar)
            manufacturer = self._resolve_manufacturer(uow, cleaned.manufacturer_name)
            attributes = self._build_attributes(uow, article_id, cleaned.attributes)
            supplier_parts = self._build_supplier_parts(
                uow, article_id, cleaned.supplier_parts
            )
            now = datetime.now(UTC)
            article = Article(
                id=article_id,
                name=cleaned.name,
                manufacturer_id=manufacturer.id if manufacturer else None,
                manufacturer_part_number=cleaned.manufacturer_part_number,
                normalized_manufacturer_part_number=(
                    normalize_part_number(cleaned.manufacturer_part_number)
                    if cleaned.manufacturer_part_number
                    else None
                ),
                category_id=category.id,
                description=cleaned.description,
                datasheet_url=cleaned.datasheet_url,
                product_url=cleaned.product_url,
                note=cleaned.note,
                search_text=self._search_text(
                    cleaned, manufacturer, category, attributes, supplier_parts
                ),
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            uow.articles.add_article(article)
            uow.articles.replace_article_attributes(article_id, attributes)
            uow.articles.replace_supplier_parts(article_id, supplier_parts)
            uow.commit()
        return self.get(article_id)

    def update(
        self,
        article_id: UUID,
        draft: ArticleDraft,
        *,
        is_active: bool | None = None,
    ) -> ArticleDetails:
        cleaned = self._clean_draft(draft)
        with self._uow_factory() as uow:
            current = uow.articles.get_article(article_id)
            if current is None:
                raise ArticleNotFoundError("Der Artikel wurde nicht gefunden.")
            category = self._require_active_category(uow, cleaned.category_id)
            duplicates = self._duplicate_candidates(
                uow, cleaned, exclude_article_id=article_id
            )
            self._enforce_duplicates(duplicates, cleaned.acknowledge_similar)
            manufacturer = self._resolve_manufacturer(uow, cleaned.manufacturer_name)
            attributes = self._build_attributes(uow, article_id, cleaned.attributes)
            supplier_parts = self._build_supplier_parts(
                uow,
                article_id,
                cleaned.supplier_parts,
                exclude_article_id=article_id,
            )
            updated = replace(
                current,
                name=cleaned.name,
                manufacturer_id=manufacturer.id if manufacturer else None,
                manufacturer_part_number=cleaned.manufacturer_part_number,
                normalized_manufacturer_part_number=(
                    normalize_part_number(cleaned.manufacturer_part_number)
                    if cleaned.manufacturer_part_number
                    else None
                ),
                category_id=category.id,
                description=cleaned.description,
                datasheet_url=cleaned.datasheet_url,
                product_url=cleaned.product_url,
                note=cleaned.note,
                search_text=self._search_text(
                    cleaned, manufacturer, category, attributes, supplier_parts
                ),
                is_active=current.is_active if is_active is None else is_active,
                updated_at=datetime.now(UTC),
            )
            uow.articles.update_article(updated)
            uow.articles.replace_article_attributes(article_id, attributes)
            uow.articles.replace_supplier_parts(article_id, supplier_parts)
            uow.commit()
        return self.get(article_id)

    @staticmethod
    def _clean_draft(draft: ArticleDraft) -> ArticleDraft:
        name = clean_text(draft.name, "Bezeichnung", 160, required=True)
        assert name is not None
        manufacturer_name = clean_text(draft.manufacturer_name, "Hersteller", 120)
        part_number = clean_text(
            draft.manufacturer_part_number, "Herstellerartikelnummer", 160
        )
        if part_number and not manufacturer_name:
            raise ValidationError(
                "Zu einer Herstellerartikelnummer muss ein Hersteller angegeben werden."
            )
        return replace(
            draft,
            name=name,
            manufacturer_name=manufacturer_name,
            manufacturer_part_number=part_number,
            description=clean_text(draft.description, "Beschreibung", 4_000),
            datasheet_url=validate_optional_url(draft.datasheet_url, "Datenblatt-Link"),
            product_url=validate_optional_url(draft.product_url, "Produkt-Link"),
            note=clean_text(draft.note, "Notiz", 4_000),
        )

    @staticmethod
    def _require_active_category(uow, category_id: UUID) -> Category:
        category = uow.articles.get_category(category_id)
        if category is None or not category.is_active:
            raise ReferenceNotFoundError(
                "Die Kategorie ist nicht aktiv oder unbekannt."
            )
        return category

    @staticmethod
    def _resolve_manufacturer(uow, name: str | None) -> Manufacturer | None:
        if not name:
            return None
        normalized = normalize_manufacturer_name(name)
        existing = uow.articles.get_manufacturer_by_normalized(normalized)
        if existing:
            if not existing.is_active:
                raise ReferenceNotFoundError("Der Hersteller ist deaktiviert.")
            return existing
        now = datetime.now(UTC)
        manufacturer = Manufacturer(
            id=uuid4(),
            name=name,
            normalized_name=normalized,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        uow.articles.add_manufacturer(manufacturer)
        return manufacturer

    def _build_attributes(
        self, uow, article_id: UUID, inputs: tuple[AttributeInput, ...]
    ) -> list[ArticleAttribute]:
        result: list[ArticleAttribute] = []
        seen_definitions: set[UUID] = set()
        for sort_order, item in enumerate(inputs, start=10):
            raw_value = clean_text(item.raw_value, "Eigenschaftswert", 240)
            if not raw_value:
                continue
            custom_name = clean_text(item.custom_name, "Eigenschaftsname", 100)
            unit = clean_text(item.unit, "Einheit", 24)
            definition: AttributeDefinition | None = None
            if item.definition_id:
                if item.definition_id in seen_definitions:
                    raise ValidationError("Eine Eigenschaft wurde mehrfach angegeben.")
                seen_definitions.add(item.definition_id)
                definition = uow.articles.get_attribute_definition(item.definition_id)
                if definition is None or not definition.is_active:
                    raise ReferenceNotFoundError(
                        "Eine Eigenschaftsdefinition ist unbekannt oder deaktiviert."
                    )
                custom_name = None
            elif not custom_name:
                raise ValidationError(
                    "Eine freie Eigenschaft benötigt eine Bezeichnung."
                )
            numeric = normalized_numeric_value(
                raw_value, definition.value_kind if definition else "text"
            )
            canonical_unit = definition.canonical_unit if definition else None
            canonical_numeric = (
                numeric if canonical_unit and unit == canonical_unit else None
            )
            result.append(
                ArticleAttribute(
                    id=uuid4(),
                    article_id=article_id,
                    attribute_definition_id=definition.id if definition else None,
                    custom_name=custom_name,
                    raw_value=raw_value,
                    normalized_text=normalize_search_text(raw_value),
                    numeric_value=numeric,
                    unit=unit,
                    canonical_numeric_value=canonical_numeric,
                    canonical_unit=canonical_unit
                    if canonical_numeric is not None
                    else None,
                    sort_order=sort_order,
                    definition_name=definition.name if definition else None,
                )
            )
        return result

    def _build_supplier_parts(
        self,
        uow,
        article_id: UUID,
        inputs: tuple[SupplierPartInput, ...],
        *,
        exclude_article_id: UUID | None = None,
    ) -> list[SupplierPart]:
        result: list[SupplierPart] = []
        seen: set[tuple[UUID, str]] = set()
        now = datetime.now(UTC)
        for item in inputs:
            number = clean_text(
                item.supplier_part_number, "Lieferantenartikelnummer", 160
            )
            if not number:
                continue
            supplier = uow.articles.get_supplier(item.supplier_id)
            if supplier is None or not supplier.is_active:
                raise ReferenceNotFoundError(
                    "Der Lieferant ist unbekannt oder deaktiviert."
                )
            normalized = normalize_part_number(number)
            key = (supplier.id, normalized)
            if key in seen:
                raise ValidationError(
                    "Eine Lieferantenartikelnummer wurde mehrfach angegeben."
                )
            seen.add(key)
            duplicate = uow.articles.find_supplier_part(
                supplier.id,
                normalized,
                exclude_article_id=exclude_article_id,
            )
            if duplicate:
                raise DuplicateArticleError(
                    "Diese Lieferantenartikelnummer gehört bereits zu einem Artikel.",
                    candidate_ids=(str(duplicate.id),),
                    match_level=1,
                    can_override=False,
                )
            result.append(
                SupplierPart(
                    id=uuid4(),
                    article_id=article_id,
                    supplier_id=supplier.id,
                    supplier_part_number=number,
                    normalized_supplier_part_number=normalized,
                    product_url=validate_optional_url(
                        item.product_url, "Lieferanten-Produktlink"
                    ),
                    created_at=now,
                    updated_at=now,
                    supplier_name=supplier.name,
                )
            )
        return result

    def _duplicate_candidates(
        self,
        uow,
        draft: ArticleDraft,
        *,
        exclude_article_id: UUID | None = None,
    ) -> list[DuplicateCandidate]:
        candidates: dict[UUID, DuplicateCandidate] = {}
        for supplier_part in draft.supplier_parts:
            number = clean_text(
                supplier_part.supplier_part_number,
                "Lieferantenartikelnummer",
                160,
            )
            if not number:
                continue
            existing = uow.articles.find_supplier_part(
                supplier_part.supplier_id,
                normalize_part_number(number),
                exclude_article_id=exclude_article_id,
            )
            if existing:
                candidates[existing.id] = DuplicateCandidate(
                    existing.id,
                    existing.name,
                    1,
                    "Gleiche Lieferantenartikelnummer",
                    False,
                )
        if draft.manufacturer_name and draft.manufacturer_part_number:
            for existing in uow.articles.find_exact_manufacturer_part(
                draft.manufacturer_name,
                draft.manufacturer_part_number,
                exclude_article_id=exclude_article_id,
            ):
                candidates[existing.id] = DuplicateCandidate(
                    existing.id,
                    existing.name,
                    2,
                    "Hersteller und Artikelnummer stimmen exakt überein",
                    False,
                )
            for existing in uow.articles.find_normalized_manufacturer_part(
                normalize_manufacturer_name(draft.manufacturer_name),
                normalize_part_number(draft.manufacturer_part_number),
                exclude_article_id=exclude_article_id,
            ):
                candidates.setdefault(
                    existing.id,
                    DuplicateCandidate(
                        existing.id,
                        existing.name,
                        3,
                        "Normalisierter Hersteller und Artikelnummer stimmen überein",
                        False,
                    ),
                )
        if not candidates:
            normalized_name = normalize_search_text(draft.name)
            for existing in uow.articles.search_articles((), include_inactive=True):
                if (
                    existing.id == exclude_article_id
                    or existing.category_id != draft.category_id
                ):
                    continue
                ratio = SequenceMatcher(
                    None, normalized_name, normalize_search_text(existing.name)
                ).ratio()
                if ratio >= 0.78:
                    candidates[existing.id] = DuplicateCandidate(
                        existing.id,
                        existing.name,
                        4,
                        "Ähnliche Bezeichnung in derselben Kategorie",
                        True,
                    )
        return sorted(
            candidates.values(),
            key=lambda candidate: (candidate.match_level, candidate.name),
        )

    @staticmethod
    def _enforce_duplicates(
        candidates: list[DuplicateCandidate], acknowledge_similar: bool
    ) -> None:
        if not candidates:
            return
        hard = [candidate for candidate in candidates if not candidate.can_override]
        if hard:
            raise DuplicateArticleError(
                "Ein vorhandener Artikel passt bereits zu diesen Identitätsdaten.",
                candidate_ids=tuple(str(item.article_id) for item in hard),
                match_level=min(item.match_level for item in hard),
                can_override=False,
            )
        if not acknowledge_similar:
            raise DuplicateArticleError(
                "Ähnliche Artikel gefunden. Prüfe sie vor dem bewussten Neuanlegen.",
                candidate_ids=tuple(str(item.article_id) for item in candidates),
                match_level=4,
                can_override=True,
            )

    @staticmethod
    def _search_text(
        draft: ArticleDraft,
        manufacturer: Manufacturer | None,
        category: Category,
        attributes: list[ArticleAttribute],
        supplier_parts: list[SupplierPart],
    ) -> str:
        values = [
            draft.name,
            manufacturer.name if manufacturer else "",
            draft.manufacturer_part_number or "",
            category.name,
            category.code,
            draft.description or "",
            draft.note or "",
            *(value.raw_value for value in attributes),
            *(value.custom_name or value.definition_name or "" for value in attributes),
            *(value.supplier_part_number for value in supplier_parts),
        ]
        return normalize_search_text(" ".join(values))

    @staticmethod
    def _details(uow, article: Article) -> ArticleDetails:
        manufacturer = (
            uow.articles.get_manufacturer(article.manufacturer_id)
            if article.manufacturer_id
            else None
        )
        category = uow.articles.get_category(article.category_id)
        if category is None:
            raise ReferenceNotFoundError("Die Artikelkategorie wurde nicht gefunden.")
        return ArticleDetails(
            article=article,
            manufacturer=manufacturer,
            category=category,
            attributes=tuple(uow.articles.list_article_attributes(article.id)),
            supplier_parts=tuple(uow.articles.list_supplier_parts(article.id)),
        )
