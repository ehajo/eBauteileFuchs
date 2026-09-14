"""Versioned REST resources for M1 locations and QR labels."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status

from ebauteilefuchs.api.dependencies import get_location_service, request_base_url
from ebauteilefuchs.api.schemas.locations import (
    BatchPreviewItemResponse,
    BatchPreviewResponse,
    BatchRequest,
    LabelSheetRequest,
    LocationCreateRequest,
    LocationPathItem,
    LocationResponse,
    LocationTreeResponse,
    LocationTypeCreateRequest,
    LocationTypeResponse,
    LocationTypeUpdateRequest,
    LocationUpdateRequest,
)
from ebauteilefuchs.application.locations import LocationDetails, LocationService
from ebauteilefuchs.application.ports.labels import LabelSheetLayout
from ebauteilefuchs.domain.locations import (
    BatchSpecification,
    LocationDraft,
    LocationType,
)

router = APIRouter(tags=["locations"])
LocationServiceDependency = Annotated[LocationService, Depends(get_location_service)]


def _type_response(location_type: LocationType) -> LocationTypeResponse:
    return LocationTypeResponse(
        id=location_type.id,
        code=location_type.code,
        name=location_type.name,
        sort_order=location_type.sort_order,
        is_system=location_type.is_system,
        is_active=location_type.is_active,
    )


def _location_response(details: LocationDetails) -> LocationResponse:
    location = details.location
    return LocationResponse(
        id=location.id,
        code=location.code,
        name=location.name,
        description=location.description,
        is_active=location.is_active,
        parent_id=location.parent_id,
        location_type=_type_response(details.location_type),
        path=[
            LocationPathItem(id=item.id, code=item.code, name=item.name)
            for item in details.path
        ],
        children_count=details.children_count,
        qr_path=f"/q/l/v1/{location.qr_token}",
        qr_short_code=location.qr_short_code,
        created_at=location.created_at,
        updated_at=location.updated_at,
        grid_columns=location.grid_columns,
        grid_rows=location.grid_rows,
    )


def _tree_response(node) -> LocationTreeResponse:
    return LocationTreeResponse(
        location=_location_response(node.details),
        children=[_tree_response(child) for child in node.children],
    )


def _batch_specification(payload: BatchRequest) -> BatchSpecification:
    return BatchSpecification(
        parent_id=payload.parent_id,
        location_type_id=payload.location_type_id,
        count=payload.count,
        start_number=payload.start_number,
        padding=payload.padding,
        code_pattern=payload.code_pattern,
        name_pattern=payload.name_pattern,
        split_into_compartments=payload.split_into_compartments,
    )


@router.get("/location-types", response_model=list[LocationTypeResponse])
def list_location_types(
    service: LocationServiceDependency,
    include_inactive: bool = False,
) -> list[LocationTypeResponse]:
    return [
        _type_response(item)
        for item in service.list_types(include_inactive=include_inactive)
    ]


@router.post(
    "/location-types",
    response_model=LocationTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_location_type(
    payload: LocationTypeCreateRequest,
    service: LocationServiceDependency,
) -> LocationTypeResponse:
    return _type_response(
        service.create_type(
            code=payload.code, name=payload.name, sort_order=payload.sort_order
        )
    )


@router.put("/location-types/{location_type_id}", response_model=LocationTypeResponse)
def update_location_type(
    location_type_id: UUID,
    payload: LocationTypeUpdateRequest,
    service: LocationServiceDependency,
) -> LocationTypeResponse:
    return _type_response(
        service.update_type(
            location_type_id,
            name=payload.name,
            sort_order=payload.sort_order,
            is_active=payload.is_active,
        )
    )


@router.get("/locations", response_model=list[LocationResponse])
def list_locations(
    service: LocationServiceDependency,
    include_inactive: bool = True,
) -> list[LocationResponse]:
    return [
        _location_response(item)
        for item in service.list_details(include_inactive=include_inactive)
    ]


@router.get("/locations/tree", response_model=list[LocationTreeResponse])
def location_tree(
    service: LocationServiceDependency,
    include_inactive: bool = True,
) -> list[LocationTreeResponse]:
    return [
        _tree_response(node)
        for node in service.list_tree(include_inactive=include_inactive)
    ]


@router.post(
    "/locations",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_location(
    payload: LocationCreateRequest,
    service: LocationServiceDependency,
) -> LocationResponse:
    return _location_response(
        service.create(
            LocationDraft(
                code=payload.code,
                name=payload.name,
                location_type_id=payload.location_type_id,
                parent_id=payload.parent_id,
                description=payload.description,
                grid_columns=payload.grid_columns,
                grid_rows=payload.grid_rows,
            )
        )
    )


@router.post("/locations/batch/preview", response_model=BatchPreviewResponse)
def preview_batch(
    payload: BatchRequest,
    service: LocationServiceDependency,
) -> BatchPreviewResponse:
    preview = service.preview_batch(_batch_specification(payload))
    return BatchPreviewResponse(
        has_conflicts=preview.has_conflicts,
        items=[
            BatchPreviewItemResponse(
                code=item.draft.code,
                name=item.draft.name,
                conflict=item.conflict,
            )
            for item in preview.items
        ],
    )


@router.post(
    "/locations/batch",
    response_model=list[LocationResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_batch(
    payload: BatchRequest,
    service: LocationServiceDependency,
) -> list[LocationResponse]:
    return [
        _location_response(item)
        for item in service.create_batch(_batch_specification(payload))
    ]


@router.get("/locations/{location_id}", response_model=LocationResponse)
def get_location(
    location_id: UUID,
    service: LocationServiceDependency,
) -> LocationResponse:
    return _location_response(service.get(location_id))


@router.patch("/locations/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: UUID,
    payload: LocationUpdateRequest,
    service: LocationServiceDependency,
) -> LocationResponse:
    current = service.get(location_id).location
    fields = payload.model_fields_set
    return _location_response(
        service.update(
            location_id,
            code=payload.code if "code" in fields else current.code,
            name=payload.name if "name" in fields else current.name,
            location_type_id=payload.location_type_id
            if "location_type_id" in fields
            else current.location_type_id,
            parent_id=payload.parent_id if "parent_id" in fields else current.parent_id,
            description=payload.description
            if "description" in fields
            else current.description,
            is_active=payload.is_active if "is_active" in fields else None,
            grid_columns=payload.grid_columns
            if "grid_columns" in fields
            else current.grid_columns,
            grid_rows=payload.grid_rows if "grid_rows" in fields else current.grid_rows,
        )
    )


@router.delete("/locations/{location_id}", response_model=LocationResponse)
def deactivate_location(
    location_id: UUID,
    service: LocationServiceDependency,
) -> LocationResponse:
    return _location_response(service.deactivate(location_id))


@router.post("/locations/{location_id}/activate", response_model=LocationResponse)
def activate_location(
    location_id: UUID,
    service: LocationServiceDependency,
) -> LocationResponse:
    return _location_response(service.activate(location_id))


@router.get("/locations/{location_id}/qr.svg")
def location_qr_svg(
    location_id: UUID,
    request: Request,
    service: LocationServiceDependency,
) -> Response:
    return Response(
        service.render_qr_svg(location_id, request_base_url(request)),
        media_type="image/svg+xml",
    )


@router.get("/locations/{location_id}/label.pdf")
def single_location_label(
    location_id: UUID,
    request: Request,
    service: LocationServiceDependency,
) -> Response:
    return Response(
        service.render_single_label(location_id, request_base_url(request)),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="location-{location_id}.pdf"'
        },
    )


@router.get("/locations/{location_id}/compact-label.pdf")
def compact_location_label(
    location_id: UUID,
    request: Request,
    service: LocationServiceDependency,
) -> Response:
    return Response(
        service.render_compact_label(location_id, request_base_url(request)),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="compact-location-{location_id}.pdf"'
            )
        },
    )


@router.post("/locations/labels.pdf")
def location_label_sheet(
    payload: LabelSheetRequest,
    request: Request,
    service: LocationServiceDependency,
) -> Response:
    layout = LabelSheetLayout(**payload.layout.model_dump())
    return Response(
        service.render_label_sheet(
            payload.location_ids, request_base_url(request), layout
        ),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="location-labels.pdf"'},
    )
