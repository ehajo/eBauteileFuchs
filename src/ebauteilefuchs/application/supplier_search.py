"""M4 supplier search and controlled import orchestration."""

from dataclasses import dataclass, replace
from uuid import UUID

from ebauteilefuchs.application.articles import ArticleDetails, ArticleService
from ebauteilefuchs.application.ports.suppliers import SupplierAdapter
from ebauteilefuchs.domain.articles import ArticleDraft, SupplierPartInput
from ebauteilefuchs.domain.errors import ValidationError
from ebauteilefuchs.domain.suppliers import SupplierProduct, SupplierSearchMode


@dataclass(frozen=True, slots=True)
class SupplierSearchResult:
    query: str
    mode: SupplierSearchMode
    local_matches: tuple[ArticleDetails, ...]
    external_matches: tuple[SupplierProduct, ...]
    external_searched: bool


class SupplierSearchService:
    def __init__(self, articles: ArticleService, adapter: SupplierAdapter) -> None:
        self._articles = articles
        self._adapter = adapter

    @property
    def configured(self) -> bool:
        return self._adapter.configured

    def search(
        self,
        query: str,
        mode: SupplierSearchMode,
        *,
        force_external: bool = False,
    ) -> SupplierSearchResult:
        cleaned = " ".join(query.split())
        if not cleaned or len(cleaned) > 160:
            raise ValidationError("Die Suche muss 1 bis 160 Zeichen enthalten.")
        exact = self._articles.find_by_supplier_number("mouser", cleaned)
        local = (
            [exact]
            if exact
            else self._articles.list_articles(query=cleaned, include_inactive=False)
        )
        external_searched = force_external or not local
        external = self._adapter.search(cleaned, mode) if external_searched else ()
        return SupplierSearchResult(
            query=cleaned,
            mode=mode,
            local_matches=tuple(local),
            external_matches=external,
            external_searched=external_searched,
        )

    def review(self, mouser_part_number: str) -> SupplierProduct:
        products = self._adapter.search(
            mouser_part_number, SupplierSearchMode.PART_NUMBER
        )
        normalized = "".join(c for c in mouser_part_number.upper() if c.isalnum())
        for product in products:
            candidate = "".join(
                c for c in product.supplier_part_number.upper() if c.isalnum()
            )
            if candidate == normalized:
                return product
        if len(products) == 1:
            return products[0]
        raise ValidationError("Der ausgewählte Mouser-Artikel wurde nicht gefunden.")

    def import_article(
        self,
        draft: ArticleDraft,
        *,
        mouser_part_number: str,
        product_url: str | None,
        existing_article_id: UUID | None = None,
    ) -> ArticleDetails:
        already = self._articles.find_by_supplier_number("mouser", mouser_part_number)
        if already:
            return already
        if existing_article_id:
            return self._articles.attach_supplier_part(
                existing_article_id,
                supplier_code="mouser",
                part_number=mouser_part_number,
                product_url=product_url,
            )
        supplier = next(
            item for item in self._articles.list_suppliers() if item.code == "mouser"
        )
        imported = replace(
            draft,
            supplier_parts=(
                *draft.supplier_parts,
                SupplierPartInput(
                    supplier_id=supplier.id,
                    supplier_part_number=mouser_part_number,
                    product_url=product_url,
                ),
            ),
        )
        return self._articles.create(imported)
