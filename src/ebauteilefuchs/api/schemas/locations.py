"""Transport schemas for M1 location resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class LocationTypeResponse(BaseModel):
    id: UUID
    code: str
    name: str
    sort_order: int
    is_system: bool
    is_active: bool


class LocationTypeCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=1, max_length=80)
    sort_order: int = Field(default=100, ge=0, le=10_000)


class LocationTypeUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    sort_order: int = Field(ge=0, le=10_000)
    is_active: bool


class LocationPathItem(BaseModel):
    id: UUID
    code: str
    name: str


class LocationResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    is_active: bool
    parent_id: UUID | None
    location_type: LocationTypeResponse
    path: list[LocationPathItem]
    children_count: int
    qr_path: str
    qr_short_code: str
    created_at: datetime
    updated_at: datetime


class LocationTreeResponse(BaseModel):
    location: LocationResponse
    children: list["LocationTreeResponse"]


class LocationCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    location_type_id: UUID
    parent_id: UUID | None = None
    description: str | None = Field(default=None, max_length=1_000)


class LocationUpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    location_type_id: UUID | None = None
    parent_id: UUID | None = None
    description: str | None = Field(default=None, max_length=1_000)
    is_active: bool | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> "LocationUpdateRequest":
        for field_name in ("code", "name", "location_type_id"):
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(f"{field_name} must not be null")
        return self


class BatchRequest(BaseModel):
    parent_id: UUID
    location_type_id: UUID
    count: int = Field(default=60, ge=1, le=200)
    start_number: int = Field(default=1, ge=0, le=999_999)
    padding: int = Field(default=2, ge=1, le=6)
    code_pattern: str = Field(default="{number_padded}", min_length=1, max_length=120)
    name_pattern: str = Field(
        default="Schublade {number_padded}", min_length=1, max_length=120
    )
    split_into_compartments: bool = False


class BatchPreviewItemResponse(BaseModel):
    code: str
    name: str
    conflict: str | None


class BatchPreviewResponse(BaseModel):
    has_conflicts: bool
    items: list[BatchPreviewItemResponse]


class LabelSheetLayoutRequest(BaseModel):
    columns: int = Field(default=3, ge=1, le=6)
    rows: int = Field(default=8, ge=1, le=20)
    label_width_mm: float = Field(default=70, ge=40, le=100)
    label_height_mm: float = Field(default=36, ge=25, le=70)
    margin_left_mm: float = Field(default=0, ge=0, le=50)
    margin_top_mm: float = Field(default=4.5, ge=0, le=50)
    horizontal_gap_mm: float = Field(default=0, ge=0, le=50)
    vertical_gap_mm: float = Field(default=0, ge=0, le=50)


class LabelSheetRequest(BaseModel):
    location_ids: list[UUID] = Field(min_length=1, max_length=500)
    layout: LabelSheetLayoutRequest = Field(default_factory=LabelSheetLayoutRequest)
