"""Responsive M4 local-first Mouser search and controlled import pages."""

import secrets
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from ebauteilefuchs.application.supplier_search import SupplierSearchService
from ebauteilefuchs.domain.articles import ArticleDraft, AttributeInput
from ebauteilefuchs.domain.errors import (
    DomainError,
    DuplicateArticleError,
    ValidationError,
)
from ebauteilefuchs.domain.suppliers import SupplierSearchMode
from ebauteilefuchs.web.locations import _render, _verify_csrf
from ebauteilefuchs.web.presentation import unit_choices

router = APIRouter(include_in_schema=False)


def _service(request: Request) -> SupplierSearchService:
    return request.app.state.supplier_search_service_factory()


def _article_service(request: Request):
    return request.app.state.article_service_factory()


def _local_cards(request: Request, matches) -> list[dict]:
    inventory = request.app.state.inventory_service_factory()
    return [
        {
            "details": item,
            "positions": inventory.list_positions(article_id=item.article.id),
            "totals": inventory.totals(item.article.id),
        }
        for item in matches
    ]


@router.get("/suppliers/mouser", response_class=HTMLResponse)
def search_page(request: Request) -> HTMLResponse:
    query = request.query_params.get("q", "")
    mode_value = request.query_params.get("mode", SupplierSearchMode.PART_NUMBER)
    force_external = request.query_params.get("external") == "1"
    result = None
    error = None
    try:
        mode = SupplierSearchMode(mode_value)
    except ValueError:
        mode = SupplierSearchMode.PART_NUMBER
        error = "Ungültiger Suchmodus."
    else:
        try:
            if query:
                result = _service(request).search(
                    query, mode, force_external=force_external
                )
        except DomainError as caught:
            error = caught.message
    return _render(
        request,
        "suppliers/search.html",
        {
            "query": result.query if result else query,
            "mode": mode,
            "configured": _service(request).configured,
            "result": result,
            "local_cards": _local_cards(request, result.local_matches)
            if result
            else [],
            "error": error,
        },
    )


@router.get("/suppliers/mouser/review", response_class=HTMLResponse)
def review_page(request: Request) -> HTMLResponse:
    part_number = request.query_params.get("part_number", "")
    try:
        product = _service(request).review(part_number)
        return _render(
            request,
            "suppliers/review.html",
            _review_context(request, product),
        )
    except DomainError as error:
        return _render(
            request,
            "suppliers/search.html",
            {
                "query": part_number,
                "mode": SupplierSearchMode.PART_NUMBER,
                "configured": _service(request).configured,
                "result": None,
                "local_cards": [],
                "error": error.message,
            },
            status_code=422,
        )


def _review_context(request: Request, product) -> dict:
    articles = _article_service(request)
    categories = articles.list_categories()
    category = next(
        (item for item in categories if item.code == product.suggested_category_code),
        next(item for item in categories if item.code == "other"),
    )
    definitions = articles.list_category_attributes(category.id)
    by_code = {item.definition.code: item.definition for item in definitions}
    mapped = []
    for item in product.attributes:
        definition = by_code.get(item.definition_code or "")
        mapped.append(
            {
                "source": item,
                "definition": definition,
                "name": definition.name if definition else item.original_name,
                "value": item.value or item.original_value,
                "unit": item.unit or "",
                "units": unit_choices(definition.canonical_unit) if definition else (),
            }
        )
    candidate_query = product.manufacturer_part_number or product.name
    candidates = articles.list_articles(query=candidate_query, include_inactive=False)
    candidate_cards = []
    for item in candidates:
        differences = []
        comparisons = (
            ("Bezeichnung", item.article.name, product.name),
            (
                "Hersteller",
                item.manufacturer.name if item.manufacturer else "nicht angegeben",
                product.manufacturer or "nicht angegeben",
            ),
            (
                "Herstellerartikelnummer",
                item.article.manufacturer_part_number or "nicht angegeben",
                product.manufacturer_part_number or "nicht angegeben",
            ),
            ("Kategorie", item.category.name, category.name),
        )
        for label, local_value, supplier_value in comparisons:
            if local_value.casefold() != supplier_value.casefold():
                differences.append(
                    {
                        "label": label,
                        "local": local_value,
                        "supplier": supplier_value,
                    }
                )
        candidate_cards.append({"details": item, "differences": differences})
    return {
        "product": product,
        "categories": categories,
        "selected_category": category,
        "mapped_attributes": mapped,
        "candidates": candidates,
        "candidate_cards": candidate_cards,
        "import_token": secrets.token_urlsafe(24),
        "error": None,
    }


@router.post("/suppliers/mouser/import", response_class=HTMLResponse)
async def import_product(request: Request) -> Response:
    form = await request.form()
    try:
        _verify_csrf(request, str(form.get("csrf_token", "")))
        token = str(form.get("import_token", ""))
        if len(token) < 16:
            raise ValidationError("Die Importprüfung ist abgelaufen. Bitte neu öffnen.")
        attributes = []
        for index in range(40):
            raw_value = str(form.get(f"attribute_value_{index}", "")).strip()
            if not raw_value:
                continue
            definition_id = str(form.get(f"attribute_definition_{index}", ""))
            custom_name = str(form.get(f"attribute_name_{index}", ""))
            attributes.append(
                AttributeInput(
                    definition_id=UUID(definition_id) if definition_id else None,
                    custom_name=None if definition_id else custom_name,
                    raw_value=raw_value,
                    unit=str(form.get(f"attribute_unit_{index}", "")),
                )
            )
        draft = ArticleDraft(
            name=str(form.get("name", "")),
            category_id=UUID(str(form.get("category_id", ""))),
            manufacturer_name=str(form.get("manufacturer_name", "")),
            manufacturer_part_number=str(form.get("manufacturer_part_number", "")),
            description=str(form.get("description", "")),
            datasheet_url=str(form.get("datasheet_url", "")),
            product_url=str(form.get("product_url", "")),
            attributes=tuple(attributes),
            acknowledge_similar=form.get("acknowledge_similar") == "true",
        )
        existing = str(form.get("existing_article_id", ""))
        imported = _service(request).import_article(
            draft,
            mouser_part_number=str(form.get("mouser_part_number", "")),
            product_url=str(form.get("product_url", "")),
            existing_article_id=UUID(existing) if existing else None,
        )
        return RedirectResponse(f"/articles/{imported.article.id}", status_code=303)
    except DuplicateArticleError as error:
        candidates = [
            _article_service(request).get(UUID(value)) for value in error.candidate_ids
        ]
        return _render(
            request,
            "suppliers/import_error.html",
            {
                "error": error.message,
                "candidates": candidates,
                "part_number": str(form.get("mouser_part_number", "")),
            },
            status_code=409,
        )
    except (DomainError, ValueError) as error:
        message = (
            error.message
            if isinstance(error, DomainError)
            else "Ungültige Importdaten."
        )
        return _render(
            request,
            "suppliers/import_error.html",
            {
                "error": message,
                "candidates": [],
                "part_number": str(form.get("mouser_part_number", "")),
            },
            status_code=422,
        )
