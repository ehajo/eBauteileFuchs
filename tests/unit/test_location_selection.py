from datetime import UTC, datetime
from uuid import UUID

from ebauteilefuchs.application.location_selection import (
    build_booking_location_selection,
)
from ebauteilefuchs.application.locations import LocationDetails
from ebauteilefuchs.domain.locations import Location, LocationType


def _details(
    number: int,
    code: str,
    *,
    parent: Location | None = None,
    children: int = 0,
) -> LocationDetails:
    identifier = UUID(f"00000000-0000-4000-8000-{number:012d}")
    location = Location(
        id=identifier,
        code=code,
        normalized_code=code.casefold(),
        name=code,
        location_type_id=UUID("10000000-0000-4000-8000-000000000001"),
        parent_id=parent.id if parent else None,
        description=None,
        is_active=True,
        qr_token=f"token-{number}",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    location_type = LocationType(
        id=location.location_type_id,
        code="box",
        name="Box",
        sort_order=1,
        is_system=True,
        is_active=True,
    )
    path = (parent, location) if parent else (location,)
    return LocationDetails(location, location_type, path, children)


def test_selection_only_offers_leafs_and_finds_free_location_in_scope() -> None:
    room = _details(1, "RAUM", children=2)
    occupied = _details(2, "01", parent=room.location)
    free = _details(3, "02", parent=room.location)
    elsewhere = _details(4, "ANDERS")

    selection = build_booking_location_selection(
        [elsewhere, free, room, occupied],
        occupied_location_ids={occupied.location.id, elsewhere.location.id},
        scope_id=room.location.id,
    )

    assert [item.location.code for item in selection.locations] == ["01", "02"]
    assert selection.next_free == free
    assert room not in selection.locations


def test_explicit_parent_selection_is_preserved_for_existing_deep_link() -> None:
    room = _details(1, "RAUM", children=1)
    box = _details(2, "BOX", parent=room.location)

    selection = build_booking_location_selection(
        [room, box],
        occupied_location_ids=set(),
        explicitly_selected_id=room.location.id,
    )

    assert room in selection.locations
    assert selection.next_free == box
