"""Prepare compact, hierarchy-aware location choices for booking workflows."""

from dataclasses import dataclass
from uuid import UUID

from ebauteilefuchs.application.locations import LocationDetails


@dataclass(frozen=True, slots=True)
class BookingLocationSelection:
    scopes: tuple[LocationDetails, ...]
    locations: tuple[LocationDetails, ...]
    next_free: LocationDetails | None


def build_location_scopes(
    details: list[LocationDetails],
) -> tuple[LocationDetails, ...]:
    """Return useful storage areas without flooding selects with leaf drawers."""

    ordered = sorted(
        details,
        key=lambda item: tuple(part.normalized_code for part in item.path),
    )
    compact_type_codes = {"drawer", "compartment"}
    return tuple(
        item
        for item in ordered
        if len(item.path) == 1
        or (
            item.location_type.code not in compact_type_codes
            and any(
                candidate.location.parent_id == item.location.id
                and candidate.location_type.code != "compartment"
                for candidate in ordered
            )
        )
    )


def build_booking_location_selection(
    details: list[LocationDetails],
    *,
    occupied_location_ids: set[UUID],
    scope_id: UUID | None = None,
    explicitly_selected_id: UUID | None = None,
) -> BookingLocationSelection:
    """Return leaf booking locations below a scope and the first empty one."""

    ordered = sorted(
        details,
        key=lambda item: tuple(part.normalized_code for part in item.path),
    )
    known_ids = {item.location.id for item in ordered}
    effective_scope = scope_id if scope_id in known_ids else None

    def in_scope(item: LocationDetails) -> bool:
        return effective_scope is None or any(
            part.id == effective_scope for part in item.path
        )

    locations = [
        item for item in ordered if item.children_count == 0 and in_scope(item)
    ]
    if explicitly_selected_id is not None and all(
        item.location.id != explicitly_selected_id for item in locations
    ):
        selected = next(
            (
                item
                for item in ordered
                if item.location.id == explicitly_selected_id and in_scope(item)
            ),
            None,
        )
        if selected is not None:
            locations.append(selected)
            locations.sort(
                key=lambda item: tuple(part.normalized_code for part in item.path)
            )

    next_free = next(
        (
            item
            for item in locations
            if item.location.id not in occupied_location_ids
            and item.children_count == 0
        ),
        None,
    )
    return BookingLocationSelection(
        scopes=build_location_scopes(details),
        locations=tuple(locations),
        next_free=next_free,
    )
