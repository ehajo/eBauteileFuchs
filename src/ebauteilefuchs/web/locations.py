"""Server-rendered M1 location workflows."""

import hmac
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from ebauteilefuchs.api.dependencies import request_base_url
from ebauteilefuchs.application.inventory import (
    ArchiveAction,
    ArchiveResolution,
    InventoryService,
)
from ebauteilefuchs.application.locations import LocationService
from ebauteilefuchs.application.ports.labels import LabelSheetLayout
from ebauteilefuchs.domain.errors import DomainError, ValidationError
from ebauteilefuchs.domain.locations import BatchSpecification, LocationDraft

router = APIRouter(include_in_schema=False)


def _service(request: Request) -> LocationService:
    return request.app.state.location_service_factory()


def _inventory_service(request: Request) -> InventoryService:
    return request.app.state.inventory_service_factory()


def _location_detail_context(
    request: Request, location_id: UUID, *, error: str | None = None
) -> dict:
    inventory = request.app.state.inventory_service_factory()
    return {
        "details": _service(request).get(location_id),
        "error": error,
        "inventory_positions": inventory.list_positions(location_id=location_id),
        "inventory_movements": inventory.list_movements(
            location_id=location_id, limit=10
        ),
    }


def _csrf_token(request: Request) -> str:
    return request.cookies.get("ebauteilefuchs_csrf") or secrets.token_urlsafe(24)


def _verify_csrf(request: Request, submitted: str) -> None:
    stored = request.cookies.get("ebauteilefuchs_csrf", "")
    if not stored or not hmac.compare_digest(stored, submitted):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Das Formular ist abgelaufen. Lade die Seite neu und versuche es erneut.",
        )


def _render(
    request: Request,
    template: str,
    context: dict,
    *,
    status_code: int = 200,
) -> HTMLResponse:
    token = _csrf_token(request)
    response = request.app.state.templates.TemplateResponse(
        request=request,
        name=template,
        context={
            "branding": request.app.state.branding,
            "version": request.app.version,
            "csrf_token": token,
            **context,
        },
        status_code=status_code,
    )
    if "ebauteilefuchs_csrf" not in request.cookies:
        response.set_cookie(
            "ebauteilefuchs_csrf",
            token,
            httponly=True,
            samesite="strict",
            secure=request.url.scheme == "https",
        )
    return response


def _error_status(error: DomainError) -> int:
    return 404 if error.code.endswith("not_found") else 422


def _optional_uuid(value: str) -> UUID | None:
    return UUID(value) if value else None


def _drawer_types(service: LocationService) -> list:
    return [item for item in service.list_types() if item.code == "drawer"]


@router.get("/locations", response_class=HTMLResponse)
def locations(request: Request) -> HTMLResponse:
    service = _service(request)
    return _render(
        request,
        "locations/list.html",
        {
            "tree": service.list_tree(include_inactive=False),
            "created": request.query_params.get("created"),
            "archived": request.query_params.get("archived"),
        },
    )


@router.get("/locations/new", response_class=HTMLResponse)
def new_location(request: Request) -> HTMLResponse:
    service = _service(request)
    selected_parent = request.query_params.get("parent_id", "")
    return _render(
        request,
        "locations/form.html",
        {
            "heading": "Lagerplatz anlegen",
            "submit_label": "Lagerplatz anlegen",
            "action": "/locations",
            "types": service.list_types(),
            "parents": service.list_details(include_inactive=False),
            "values": {"parent_id": selected_parent},
            "error": None,
        },
    )


@router.post("/locations", response_class=HTMLResponse)
def create_location(
    request: Request,
    csrf_token: str = Form(),
    code: str = Form(),
    name: str = Form(),
    location_type_id: str = Form(),
    parent_id: str = Form(default=""),
    description: str = Form(default=""),
) -> Response:
    _verify_csrf(request, csrf_token)
    service = _service(request)
    values = {
        "code": code,
        "name": name,
        "location_type_id": location_type_id,
        "parent_id": parent_id,
        "description": description,
    }
    try:
        created = service.create(
            LocationDraft(
                code=code,
                name=name,
                location_type_id=UUID(location_type_id),
                parent_id=_optional_uuid(parent_id),
                description=description,
            )
        )
    except (DomainError, ValueError) as error:
        message = (
            error.message if isinstance(error, DomainError) else "Ungültige Auswahl."
        )
        return _render(
            request,
            "locations/form.html",
            {
                "heading": "Lagerplatz anlegen",
                "submit_label": "Lagerplatz anlegen",
                "action": "/locations",
                "types": service.list_types(),
                "parents": service.list_details(include_inactive=False),
                "values": values,
                "error": message,
            },
            status_code=422,
        )
    return RedirectResponse(f"/locations/{created.location.id}", status_code=303)


@router.get("/locations/magazine/new", response_class=HTMLResponse)
def new_magazine(request: Request) -> HTMLResponse:
    service = _service(request)
    return _render(
        request,
        "locations/batch.html",
        {
            "types": _drawer_types(service),
            "parents": service.list_details(include_inactive=False),
            "values": {},
            "preview": None,
            "error": None,
        },
    )


def _batch_spec(
    parent_id: str,
    location_type_id: str,
    magazine_code: str,
    magazine_name: str,
    count: int,
    start_number: int,
    padding: int,
    code_pattern: str,
    name_pattern: str,
    split_into_compartments: bool,
) -> BatchSpecification:
    return BatchSpecification(
        parent_id=UUID(parent_id),
        location_type_id=UUID(location_type_id),
        magazine_code=magazine_code,
        magazine_name=magazine_name,
        count=count,
        start_number=start_number,
        padding=padding,
        code_pattern=code_pattern,
        name_pattern=name_pattern,
        split_into_compartments=split_into_compartments,
    )


def _batch_values(**values) -> dict:
    return values


@router.post("/locations/magazine/preview", response_class=HTMLResponse)
def preview_magazine(
    request: Request,
    csrf_token: str = Form(),
    parent_id: str = Form(),
    location_type_id: str = Form(),
    magazine_code: str = Form(),
    magazine_name: str = Form(),
    count: int = Form(default=60),
    start_number: int = Form(default=1),
    padding: int = Form(default=2),
    code_pattern: str = Form(default="{number_padded}"),
    name_pattern: str = Form(default="Schublade {number_padded}"),
    split_into_compartments: bool = Form(default=False),
) -> HTMLResponse:
    _verify_csrf(request, csrf_token)
    service = _service(request)
    values = _batch_values(
        parent_id=parent_id,
        location_type_id=location_type_id,
        magazine_code=magazine_code,
        magazine_name=magazine_name,
        count=count,
        start_number=start_number,
        padding=padding,
        code_pattern=code_pattern,
        name_pattern=name_pattern,
        split_into_compartments=split_into_compartments,
    )
    try:
        preview = service.preview_batch(_batch_spec(**values))
        error = None
    except (DomainError, ValueError) as exc:
        preview = None
        error = exc.message if isinstance(exc, DomainError) else "Ungültige Auswahl."
    return _render(
        request,
        "locations/batch.html",
        {
            "types": _drawer_types(service),
            "parents": service.list_details(include_inactive=False),
            "values": values,
            "preview": preview,
            "error": error,
        },
        status_code=422 if error else 200,
    )


@router.post("/locations/magazine/create")
def create_magazine(
    request: Request,
    csrf_token: str = Form(),
    parent_id: str = Form(),
    location_type_id: str = Form(),
    magazine_code: str = Form(),
    magazine_name: str = Form(),
    count: int = Form(),
    start_number: int = Form(),
    padding: int = Form(),
    code_pattern: str = Form(),
    name_pattern: str = Form(),
    split_into_compartments: bool = Form(default=False),
) -> Response:
    _verify_csrf(request, csrf_token)
    service = _service(request)
    values = _batch_values(
        parent_id=parent_id,
        location_type_id=location_type_id,
        magazine_code=magazine_code,
        magazine_name=magazine_name,
        count=count,
        start_number=start_number,
        padding=padding,
        code_pattern=code_pattern,
        name_pattern=name_pattern,
        split_into_compartments=split_into_compartments,
    )
    try:
        created = service.create_batch(_batch_spec(**values))
    except (DomainError, ValueError) as error:
        message = (
            error.message if isinstance(error, DomainError) else "Ungültige Auswahl."
        )
        return _render(
            request,
            "locations/batch.html",
            {
                "types": _drawer_types(service),
                "parents": service.list_details(include_inactive=False),
                "values": values,
                "preview": None,
                "error": message,
            },
            status_code=422,
        )
    return RedirectResponse(f"/locations?created={len(created)}", status_code=303)


@router.post("/locations/group/preview", response_class=HTMLResponse)
def preview_group_locations(
    request: Request,
    location_ids: Annotated[list[UUID], Form()],
    csrf_token: str = Form(),
) -> HTMLResponse:
    _verify_csrf(request, csrf_token)
    service = _service(request)
    return _render(
        request,
        "locations/group.html",
        {
            "locations": [service.get(item) for item in location_ids],
            "location_ids": location_ids,
            "error": None,
        },
    )


@router.post("/locations/group", response_class=HTMLResponse)
def group_locations(
    request: Request,
    location_ids: Annotated[list[UUID], Form()],
    csrf_token: str = Form(),
    code: str = Form(),
    name: str = Form(),
) -> Response:
    _verify_csrf(request, csrf_token)
    service = _service(request)
    try:
        magazine = service.group_into_magazine(location_ids, code=code, name=name)
    except DomainError as error:
        return _render(
            request,
            "locations/group.html",
            {
                "locations": [service.get(item) for item in location_ids],
                "location_ids": location_ids,
                "error": error.message,
            },
            status_code=422,
        )
    return RedirectResponse(f"/locations/{magazine.location.id}", status_code=303)


def _archive_context(request: Request, location_ids: list[UUID]) -> dict:
    location_service = _service(request)
    preview = _inventory_service(request).preview_location_archive(location_ids)
    articles: dict[UUID, dict] = {}
    for position in preview.positions:
        entry = articles.setdefault(
            position.balance.article_id,
            {
                "id": position.balance.article_id,
                "name": position.article_name,
                "positions": [],
            },
        )
        entry["positions"].append(position)
    subtree = set(preview.location_ids)
    targets = [
        item
        for item in location_service.list_details(include_inactive=False)
        if item.location.id not in subtree and item.children_count == 0
    ]
    return {
        "selected": [location_service.get(item) for item in location_ids],
        "location_ids": location_ids,
        "subtree_count": len(preview.location_ids),
        "articles": sorted(articles.values(), key=lambda item: item["name"].casefold()),
        "targets": targets,
        "idempotency_key": secrets.token_urlsafe(24),
        "error": None,
    }


@router.post("/locations/archive/preview", response_class=HTMLResponse)
def preview_archive_locations(
    request: Request,
    location_ids: Annotated[list[UUID], Form()],
    csrf_token: str = Form(),
) -> HTMLResponse:
    _verify_csrf(request, csrf_token)
    return _render(
        request,
        "locations/archive.html",
        _archive_context(request, location_ids),
    )


@router.post("/locations/archive", response_class=HTMLResponse)
async def archive_locations(request: Request) -> Response:
    form = await request.form()
    _verify_csrf(request, str(form.get("csrf_token", "")))
    try:
        location_ids = [UUID(str(item)) for item in form.getlist("location_ids")]
        preview = _inventory_service(request).preview_location_archive(location_ids)
        article_ids = {item.balance.article_id for item in preview.positions}
        resolutions: list[ArchiveResolution] = []
        for article_id in article_ids:
            action = ArchiveAction(str(form.get(f"action_{article_id}", "")))
            target_value = str(form.get(f"target_{article_id}", ""))
            resolutions.append(
                ArchiveResolution(
                    article_id=article_id,
                    action=action,
                    target_location_id=UUID(target_value) if target_value else None,
                )
            )
        result = _inventory_service(request).archive_locations(
            location_ids=location_ids,
            resolutions=resolutions,
            idempotency_key=str(form.get("idempotency_key", "")),
        )
    except (DomainError, ValueError) as error:
        context = _archive_context(
            request, location_ids if "location_ids" in locals() else []
        )
        context["error"] = (
            error.message if isinstance(error, DomainError) else "Prüfe alle Auswahlen."
        )
        return _render(
            request,
            "locations/archive.html",
            context,
            status_code=422,
        )
    return RedirectResponse(
        f"/locations?archived={len(result.archived_location_ids)}", status_code=303
    )


@router.post("/locations/labels.pdf")
def selected_labels(
    request: Request,
    location_ids: Annotated[list[UUID], Form()],
    csrf_token: str = Form(),
) -> Response:
    _verify_csrf(request, csrf_token)
    pdf = _service(request).render_label_sheet(
        location_ids,
        request_base_url(request),
        LabelSheetLayout(),
    )
    return Response(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="lagerplatz-etiketten.pdf"'
        },
    )


@router.get("/locations/types", response_class=HTMLResponse)
def location_types(request: Request) -> HTMLResponse:
    return _render(
        request,
        "locations/types.html",
        {"types": _service(request).list_types(include_inactive=True), "error": None},
    )


@router.post("/locations/types", response_class=HTMLResponse)
def create_location_type(
    request: Request,
    csrf_token: str = Form(),
    code: str = Form(),
    name: str = Form(),
    sort_order: int = Form(default=100),
) -> Response:
    _verify_csrf(request, csrf_token)
    service = _service(request)
    try:
        service.create_type(code=code, name=name, sort_order=sort_order)
    except DomainError as error:
        return _render(
            request,
            "locations/types.html",
            {
                "types": service.list_types(include_inactive=True),
                "error": error.message,
            },
            status_code=_error_status(error),
        )
    return RedirectResponse("/locations/types", status_code=303)


@router.post("/locations/types/{location_type_id}", response_class=HTMLResponse)
def update_location_type(
    location_type_id: UUID,
    request: Request,
    csrf_token: str = Form(),
    name: str = Form(),
    sort_order: int = Form(),
    is_active: bool = Form(),
) -> Response:
    _verify_csrf(request, csrf_token)
    service = _service(request)
    try:
        service.update_type(
            location_type_id,
            name=name,
            sort_order=sort_order,
            is_active=is_active,
        )
    except DomainError as error:
        return _render(
            request,
            "locations/types.html",
            {
                "types": service.list_types(include_inactive=True),
                "error": error.message,
            },
            status_code=_error_status(error),
        )
    return RedirectResponse("/locations/types", status_code=303)


@router.get("/locations/{location_id}/edit", response_class=HTMLResponse)
def edit_location(location_id: UUID, request: Request) -> HTMLResponse:
    service = _service(request)
    details = service.get(location_id)
    location = details.location
    return _render(
        request,
        "locations/form.html",
        {
            "heading": "Lagerplatz bearbeiten",
            "submit_label": "Änderungen speichern",
            "action": f"/locations/{location_id}/edit",
            "types": service.list_types(include_inactive=True),
            "parents": [
                item
                for item in service.list_details(include_inactive=False)
                if item.location.id != location_id
            ],
            "values": {
                "code": location.code,
                "name": location.name,
                "location_type_id": str(location.location_type_id),
                "parent_id": str(location.parent_id or ""),
                "description": location.description or "",
            },
            "error": None,
        },
    )


@router.post("/locations/{location_id}/edit", response_class=HTMLResponse)
def update_location(
    location_id: UUID,
    request: Request,
    csrf_token: str = Form(),
    code: str = Form(),
    name: str = Form(),
    location_type_id: str = Form(),
    parent_id: str = Form(default=""),
    description: str = Form(default=""),
) -> Response:
    _verify_csrf(request, csrf_token)
    service = _service(request)
    values = {
        "code": code,
        "name": name,
        "location_type_id": location_type_id,
        "parent_id": parent_id,
        "description": description,
    }
    try:
        service.update(
            location_id,
            code=code,
            name=name,
            location_type_id=UUID(location_type_id),
            parent_id=_optional_uuid(parent_id),
            description=description,
        )
    except (DomainError, ValueError) as error:
        message = (
            error.message if isinstance(error, DomainError) else "Ungültige Auswahl."
        )
        return _render(
            request,
            "locations/form.html",
            {
                "heading": "Lagerplatz bearbeiten",
                "submit_label": "Änderungen speichern",
                "action": f"/locations/{location_id}/edit",
                "types": service.list_types(include_inactive=True),
                "parents": [
                    item
                    for item in service.list_details(include_inactive=False)
                    if item.location.id != location_id
                ],
                "values": values,
                "error": message,
            },
            status_code=422,
        )
    return RedirectResponse(f"/locations/{location_id}", status_code=303)


@router.post("/locations/{location_id}/deactivate")
def deactivate_location(
    location_id: UUID, request: Request, csrf_token: str = Form()
) -> Response:
    _verify_csrf(request, csrf_token)
    service = _service(request)
    try:
        service.deactivate(location_id)
    except DomainError as error:
        return _render(
            request,
            "locations/detail.html",
            _location_detail_context(request, location_id, error=error.message),
            status_code=409,
        )
    return RedirectResponse(f"/locations/{location_id}", status_code=303)


@router.post("/locations/{location_id}/activate")
def activate_location(
    location_id: UUID, request: Request, csrf_token: str = Form()
) -> Response:
    _verify_csrf(request, csrf_token)
    service = _service(request)
    try:
        service.activate(location_id)
    except DomainError as error:
        return _render(
            request,
            "locations/detail.html",
            _location_detail_context(request, location_id, error=error.message),
            status_code=409,
        )
    return RedirectResponse(f"/locations/{location_id}", status_code=303)


@router.get("/locations/{location_id}/delete", response_class=HTMLResponse)
def delete_location_confirmation(location_id: UUID, request: Request) -> HTMLResponse:
    return _render(
        request,
        "locations/delete.html",
        {"details": _service(request).get(location_id), "error": None},
    )


@router.post("/locations/{location_id}/delete", response_class=HTMLResponse)
def delete_location(
    location_id: UUID,
    request: Request,
    csrf_token: str = Form(),
    confirm: str = Form(),
) -> Response:
    _verify_csrf(request, csrf_token)
    if confirm != "yes":
        raise ValidationError("Bestätige das endgültige Löschen.")
    service = _service(request)
    try:
        service.remove(location_id)
    except DomainError as error:
        return _render(
            request,
            "locations/delete.html",
            {"details": service.get(location_id), "error": error.message},
            status_code=409,
        )
    return RedirectResponse("/locations", status_code=303)


@router.get("/locations/{location_id}", response_class=HTMLResponse)
def location_details(location_id: UUID, request: Request) -> HTMLResponse:
    return _render(
        request,
        "locations/detail.html",
        _location_detail_context(request, location_id),
    )


@router.get("/q/l/v1/{qr_token}")
def resolve_location_qr(qr_token: str, request: Request) -> RedirectResponse:
    details = _service(request).get_by_qr_token(qr_token)
    return RedirectResponse(f"/locations/{details.location.id}", status_code=303)
