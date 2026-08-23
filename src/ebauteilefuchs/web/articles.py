"""Server-rendered M2 article catalog workflows."""

from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from ebauteilefuchs.application.articles import ArticleDetails, ArticleService
from ebauteilefuchs.domain.articles import (
    ArticleDraft,
    AttributeInput,
    SupplierPartInput,
)
from ebauteilefuchs.domain.errors import DomainError, DuplicateArticleError
from ebauteilefuchs.web.locations import _render, _verify_csrf

router = APIRouter(include_in_schema=False)


def _service(request: Request) -> ArticleService:
    return request.app.state.article_service_factory()


def _form_context(
    service: ArticleService,
    *,
    values: dict,
    action: str,
    heading: str,
    submit_label: str,
    error: str | None = None,
    duplicate_candidates: list[ArticleDetails] | None = None,
    can_override: bool = False,
) -> dict:
    category_id = values.get("category_id")
    selected_category = None
    definitions = []
    if category_id:
        try:
            selected_id = UUID(str(category_id))
            selected_category = next(
                (
                    item
                    for item in service.list_categories(include_inactive=True)
                    if item.id == selected_id
                ),
                None,
            )
            definitions = service.list_category_attributes(selected_id)
        except (ValueError, DomainError):
            pass
    return {
        "heading": heading,
        "submit_label": submit_label,
        "action": action,
        "values": values,
        "categories": service.list_categories(include_inactive=True),
        "selected_category": selected_category,
        "definitions": definitions,
        "manufacturers": service.list_manufacturers(include_inactive=True),
        "suppliers": service.list_suppliers(),
        "error": error,
        "duplicate_candidates": duplicate_candidates or [],
        "can_override": can_override,
    }


def _values_from_details(details: ArticleDetails) -> dict:
    return {
        "name": details.article.name,
        "category_id": str(details.article.category_id),
        "manufacturer_name": details.manufacturer.name if details.manufacturer else "",
        "manufacturer_part_number": details.article.manufacturer_part_number or "",
        "description": details.article.description or "",
        "datasheet_url": details.article.datasheet_url or "",
        "product_url": details.article.product_url or "",
        "note": details.article.note or "",
        "is_active": details.article.is_active,
        "attributes": {
            str(value.attribute_definition_id): {
                "raw_value": value.raw_value,
                "unit": value.unit or "",
            }
            for value in details.attributes
            if value.attribute_definition_id
        },
        "custom_attributes": [
            {
                "name": value.custom_name or "",
                "raw_value": value.raw_value,
                "unit": value.unit or "",
            }
            for value in details.attributes
            if value.custom_name
        ],
        "supplier_parts": [
            {
                "supplier_id": str(value.supplier_id),
                "supplier_part_number": value.supplier_part_number,
                "product_url": value.product_url or "",
            }
            for value in details.supplier_parts
        ],
    }


async def _parse_article_form(request: Request) -> tuple[str, ArticleDraft, dict]:
    form = await request.form()
    csrf_token = str(form.get("csrf_token", ""))
    category_id = str(form.get("category_id", ""))
    attributes: list[AttributeInput] = []
    attribute_values: dict[str, dict[str, str]] = {}
    for key, value in form.multi_items():
        if not key.startswith("attribute_") or not str(value).strip():
            continue
        definition_id = key.removeprefix("attribute_")
        unit = str(form.get(f"unit_{definition_id}", ""))
        attributes.append(
            AttributeInput(
                definition_id=UUID(definition_id),
                raw_value=str(value),
                unit=unit,
            )
        )
        attribute_values[definition_id] = {
            "raw_value": str(value),
            "unit": unit,
        }
    custom_attributes: list[dict[str, str]] = []
    for index in range(1, 4):
        name = str(form.get(f"custom_name_{index}", ""))
        raw_value = str(form.get(f"custom_value_{index}", ""))
        unit = str(form.get(f"custom_unit_{index}", ""))
        if name or raw_value:
            attributes.append(
                AttributeInput(custom_name=name, raw_value=raw_value, unit=unit)
            )
            custom_attributes.append(
                {"name": name, "raw_value": raw_value, "unit": unit}
            )
    supplier_parts: list[SupplierPartInput] = []
    supplier_values: list[dict[str, str]] = []
    for index in range(1, 4):
        supplier_id = str(form.get(f"supplier_id_{index}", ""))
        number = str(form.get(f"supplier_number_{index}", ""))
        product_url = str(form.get(f"supplier_url_{index}", ""))
        if supplier_id and number:
            supplier_parts.append(
                SupplierPartInput(
                    supplier_id=UUID(supplier_id),
                    supplier_part_number=number,
                    product_url=product_url,
                )
            )
            supplier_values.append(
                {
                    "supplier_id": supplier_id,
                    "supplier_part_number": number,
                    "product_url": product_url,
                }
            )
    values = {
        "name": str(form.get("name", "")),
        "category_id": category_id,
        "manufacturer_name": str(form.get("manufacturer_name", "")),
        "manufacturer_part_number": str(form.get("manufacturer_part_number", "")),
        "description": str(form.get("description", "")),
        "datasheet_url": str(form.get("datasheet_url", "")),
        "product_url": str(form.get("product_url", "")),
        "note": str(form.get("note", "")),
        "is_active": form.get("is_active", "true") == "true",
        "attributes": attribute_values,
        "custom_attributes": custom_attributes,
        "supplier_parts": supplier_values,
    }
    return (
        csrf_token,
        ArticleDraft(
            name=values["name"],
            category_id=UUID(category_id),
            manufacturer_name=values["manufacturer_name"],
            manufacturer_part_number=values["manufacturer_part_number"],
            description=values["description"],
            datasheet_url=values["datasheet_url"],
            product_url=values["product_url"],
            note=values["note"],
            attributes=tuple(attributes),
            supplier_parts=tuple(supplier_parts),
            acknowledge_similar=form.get("acknowledge_similar") == "true",
        ),
        values,
    )


@router.get("/articles", response_class=HTMLResponse)
def articles(request: Request) -> HTMLResponse:
    query = request.query_params.get("q", "")
    return _render(
        request,
        "articles/list.html",
        {
            "articles": _service(request).list_articles(
                query=query or None, include_inactive=True
            ),
            "query": query,
        },
    )


@router.get("/articles/new", response_class=HTMLResponse)
def new_article(request: Request) -> HTMLResponse:
    service = _service(request)
    category_id = request.query_params.get("category_id", "")
    if not category_id:
        return _render(
            request,
            "articles/category_choice.html",
            {"categories": service.list_categories()},
        )
    values = {
        "category_id": category_id,
        "attributes": {},
        "custom_attributes": [],
        "supplier_parts": [],
    }
    return _render(
        request,
        "articles/form.html",
        _form_context(
            service,
            values=values,
            action="/articles",
            heading="Artikel anlegen",
            submit_label="Artikel prüfen und anlegen",
        ),
    )


@router.post("/articles", response_class=HTMLResponse)
async def create_article(request: Request) -> Response:
    service = _service(request)
    try:
        csrf_token, draft, values = await _parse_article_form(request)
        _verify_csrf(request, csrf_token)
        created = service.create(draft)
    except DuplicateArticleError as error:
        candidates = [service.get(UUID(value)) for value in error.candidate_ids]
        return _render(
            request,
            "articles/form.html",
            _form_context(
                service,
                values=values,
                action="/articles",
                heading="Artikel anlegen",
                submit_label="Artikel prüfen und anlegen",
                error=error.message,
                duplicate_candidates=candidates,
                can_override=error.can_override,
            ),
            status_code=409,
        )
    except (DomainError, ValueError) as error:
        message = (
            error.message if isinstance(error, DomainError) else "Ungültige Auswahl."
        )
        return _render(
            request,
            "articles/form.html",
            _form_context(
                service,
                values=locals().get("values", {}),
                action="/articles",
                heading="Artikel anlegen",
                submit_label="Artikel prüfen und anlegen",
                error=message,
            ),
            status_code=422,
        )
    return RedirectResponse(f"/articles/{created.article.id}", status_code=303)


@router.get("/articles/{article_id}/edit", response_class=HTMLResponse)
def edit_article(article_id: UUID, request: Request) -> HTMLResponse:
    service = _service(request)
    details = service.get(article_id)
    return _render(
        request,
        "articles/form.html",
        _form_context(
            service,
            values=_values_from_details(details),
            action=f"/articles/{article_id}/edit",
            heading="Artikel bearbeiten",
            submit_label="Änderungen prüfen und speichern",
        ),
    )


@router.post("/articles/{article_id}/edit", response_class=HTMLResponse)
async def update_article(article_id: UUID, request: Request) -> Response:
    service = _service(request)
    try:
        csrf_token, draft, values = await _parse_article_form(request)
        _verify_csrf(request, csrf_token)
        updated = service.update(
            article_id, draft, is_active=values.get("is_active", True)
        )
    except DuplicateArticleError as error:
        candidates = [service.get(UUID(value)) for value in error.candidate_ids]
        return _render(
            request,
            "articles/form.html",
            _form_context(
                service,
                values=values,
                action=f"/articles/{article_id}/edit",
                heading="Artikel bearbeiten",
                submit_label="Änderungen prüfen und speichern",
                error=error.message,
                duplicate_candidates=candidates,
                can_override=error.can_override,
            ),
            status_code=409,
        )
    except (DomainError, ValueError) as error:
        message = (
            error.message if isinstance(error, DomainError) else "Ungültige Auswahl."
        )
        return _render(
            request,
            "articles/form.html",
            _form_context(
                service,
                values=locals().get("values", {}),
                action=f"/articles/{article_id}/edit",
                heading="Artikel bearbeiten",
                submit_label="Änderungen prüfen und speichern",
                error=message,
            ),
            status_code=422,
        )
    return RedirectResponse(f"/articles/{updated.article.id}", status_code=303)


@router.get("/articles/{article_id}", response_class=HTMLResponse)
def article_details(article_id: UUID, request: Request) -> HTMLResponse:
    return _render(
        request,
        "articles/detail.html",
        {"details": _service(request).get(article_id)},
    )
