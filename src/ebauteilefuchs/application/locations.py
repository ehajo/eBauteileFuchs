"""Use cases for location hierarchy management and label preparation."""

import re
import secrets
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from ebauteilefuchs.application.ports.labels import (
    LabelData,
    LabelRenderer,
    LabelSheetLayout,
)
from ebauteilefuchs.application.ports.locations import LocationUnitOfWorkFactory
from ebauteilefuchs.domain.errors import (
    ActiveChildrenError,
    BatchConflictError,
    DuplicateLocationCodeError,
    InactiveLocationError,
    LocationCycleError,
    LocationNotFoundError,
    LocationTypeNotFoundError,
    ValidationError,
)
from ebauteilefuchs.domain.locations import (
    BatchSpecification,
    Location,
    LocationDraft,
    LocationType,
    clean_description,
    clean_required_text,
    normalize_location_code,
)


@dataclass(frozen=True, slots=True)
class LocationDetails:
    location: Location
    location_type: LocationType
    path: tuple[Location, ...]
    children_count: int


@dataclass(frozen=True, slots=True)
class LocationTreeNode:
    details: LocationDetails
    children: tuple["LocationTreeNode", ...]


@dataclass(frozen=True, slots=True)
class BatchPreviewItem:
    draft: LocationDraft
    normalized_code: str
    conflict: str | None


@dataclass(frozen=True, slots=True)
class BatchPreview:
    specification: BatchSpecification
    items: tuple[BatchPreviewItem, ...]

    @property
    def has_conflicts(self) -> bool:
        return any(item.conflict for item in self.items)


class LocationService:
    def __init__(
        self,
        uow_factory: LocationUnitOfWorkFactory,
        label_renderer: LabelRenderer | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._label_renderer = label_renderer

    def list_types(self, *, include_inactive: bool = False) -> list[LocationType]:
        with self._uow_factory() as uow:
            return uow.locations.list_types(include_inactive=include_inactive)

    def create_type(
        self, *, code: str, name: str, sort_order: int = 100
    ) -> LocationType:
        cleaned_code = code.strip().casefold()
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,39}", cleaned_code):
            raise ValidationError(
                "Der Typcode muss 2 bis 40 Kleinbuchstaben, Ziffern oder "
                "Unterstriche enthalten und mit einem Buchstaben beginnen."
            )
        cleaned_name = clean_required_text(name, "Bezeichnung", 80)
        if not 0 <= sort_order <= 10_000:
            raise ValidationError("Die Sortierung muss zwischen 0 und 10000 liegen.")
        with self._uow_factory() as uow:
            if uow.locations.get_type_by_code(cleaned_code):
                raise DuplicateLocationCodeError(
                    "Ein Lagerplatztyp mit diesem Code ist bereits vorhanden."
                )
            location_type = LocationType(
                id=uuid4(),
                code=cleaned_code,
                name=cleaned_name,
                sort_order=sort_order,
                is_system=False,
                is_active=True,
            )
            uow.locations.add_type(location_type)
            uow.commit()
            return location_type

    def update_type(
        self,
        location_type_id: UUID,
        *,
        name: str,
        sort_order: int,
        is_active: bool,
    ) -> LocationType:
        cleaned_name = clean_required_text(name, "Bezeichnung", 80)
        if not 0 <= sort_order <= 10_000:
            raise ValidationError("Die Sortierung muss zwischen 0 und 10000 liegen.")
        with self._uow_factory() as uow:
            location_type = self._require_type(uow.locations.get_type(location_type_id))
            updated = replace(
                location_type,
                name=cleaned_name,
                sort_order=sort_order,
                is_active=is_active,
            )
            uow.locations.update_type(updated)
            uow.commit()
            return updated

    def list_details(self, *, include_inactive: bool = True) -> list[LocationDetails]:
        with self._uow_factory() as uow:
            locations = uow.locations.list_locations(include_inactive=include_inactive)
            types = {
                location_type.id: location_type
                for location_type in uow.locations.list_types(include_inactive=True)
            }
            by_id = {location.id: location for location in locations}
            child_counts: dict[UUID, int] = {}
            for location in locations:
                if location.parent_id is not None:
                    child_counts[location.parent_id] = (
                        child_counts.get(location.parent_id, 0) + 1
                    )
            return [
                LocationDetails(
                    location=location,
                    location_type=types[location.location_type_id],
                    path=self._path_from_map(location, by_id),
                    children_count=child_counts.get(location.id, 0),
                )
                for location in locations
            ]

    def list_tree(self, *, include_inactive: bool = True) -> list[LocationTreeNode]:
        details = self.list_details(include_inactive=include_inactive)
        by_parent: dict[UUID | None, list[LocationDetails]] = {}
        for item in details:
            by_parent.setdefault(item.location.parent_id, []).append(item)
        for children in by_parent.values():
            children.sort(
                key=lambda detail: (
                    detail.location.normalized_code,
                    detail.location.name.casefold(),
                )
            )

        def build(parent_id: UUID | None) -> list[LocationTreeNode]:
            return [
                LocationTreeNode(
                    details=item,
                    children=tuple(build(item.location.id)),
                )
                for item in by_parent.get(parent_id, [])
            ]

        return build(None)

    def get(self, location_id: UUID) -> LocationDetails:
        with self._uow_factory() as uow:
            location = self._require_location(uow.locations.get(location_id))
            location_type = self._require_type(
                uow.locations.get_type(location.location_type_id)
            )
            path = self._load_path(uow, location)
            children = uow.locations.list_children(location.id, include_inactive=True)
            return LocationDetails(location, location_type, path, len(children))

    def get_by_qr_token(self, qr_token: str) -> LocationDetails:
        with self._uow_factory() as uow:
            location = self._require_location(
                uow.locations.get_by_qr_token(qr_token),
                "Der QR-Code gehört zu keinem bekannten Lagerplatz.",
            )
            location_type = self._require_type(
                uow.locations.get_type(location.location_type_id)
            )
            path = self._load_path(uow, location)
            children = uow.locations.list_children(location.id, include_inactive=True)
            return LocationDetails(location, location_type, path, len(children))

    def create(self, draft: LocationDraft) -> LocationDetails:
        code, normalized_code, name, description = self._clean_draft(draft)
        with self._uow_factory() as uow:
            self._validate_type_and_parent(uow, draft.location_type_id, draft.parent_id)
            self._ensure_unique(uow, draft.parent_id, normalized_code)
            now = datetime.now(UTC)
            location = Location(
                id=uuid4(),
                code=code,
                normalized_code=normalized_code,
                name=name,
                location_type_id=draft.location_type_id,
                parent_id=draft.parent_id,
                description=description,
                is_active=True,
                qr_token=self._new_qr_token(uow),
                created_at=now,
                updated_at=now,
            )
            uow.locations.add(location)
            uow.commit()
        return self.get(location.id)

    def update(
        self,
        location_id: UUID,
        *,
        code: str,
        name: str,
        location_type_id: UUID,
        parent_id: UUID | None,
        description: str | None,
        is_active: bool | None = None,
    ) -> LocationDetails:
        cleaned_code = clean_required_text(code, "Kennung", 64)
        normalized_code = normalize_location_code(cleaned_code)
        cleaned_name = clean_required_text(name, "Bezeichnung", 120)
        cleaned_description = clean_description(description)

        with self._uow_factory() as uow:
            location = self._require_location(uow.locations.get(location_id))
            self._validate_type_and_parent(uow, location_type_id, parent_id)
            self._ensure_not_cycle(uow, location_id, parent_id)
            self._ensure_unique(uow, parent_id, normalized_code, exclude_id=location_id)
            target_active = location.is_active if is_active is None else is_active
            if not target_active:
                self._ensure_can_deactivate(uow, location_id)
            updated = replace(
                location,
                code=cleaned_code,
                normalized_code=normalized_code,
                name=cleaned_name,
                location_type_id=location_type_id,
                parent_id=parent_id,
                description=cleaned_description,
                is_active=target_active,
                updated_at=datetime.now(UTC),
            )
            uow.locations.update(updated)
            uow.commit()
        return self.get(location_id)

    def deactivate(self, location_id: UUID) -> LocationDetails:
        with self._uow_factory() as uow:
            location = self._require_location(uow.locations.get(location_id))
            if not location.is_active:
                return self.get(location_id)
            self._ensure_can_deactivate(uow, location_id)
            uow.locations.update(
                replace(location, is_active=False, updated_at=datetime.now(UTC))
            )
            uow.commit()
        return self.get(location_id)

    def activate(self, location_id: UUID) -> LocationDetails:
        with self._uow_factory() as uow:
            location = self._require_location(uow.locations.get(location_id))
            if location.parent_id is not None:
                parent = self._require_location(uow.locations.get(location.parent_id))
                if not parent.is_active:
                    raise InactiveLocationError(
                        "Der übergeordnete Lagerplatz ist deaktiviert. "
                        "Aktiviere ihn zuerst."
                    )
            if not location.is_active:
                uow.locations.update(
                    replace(location, is_active=True, updated_at=datetime.now(UTC))
                )
                uow.commit()
        return self.get(location_id)

    def remove(self, location_id: UUID) -> None:
        """Permanently remove an unused location without inventory history."""

        with self._uow_factory() as uow:
            location = self._require_location(uow.locations.get(location_id))
            children = uow.locations.list_children(location.id, include_inactive=True)
            if children:
                raise ActiveChildrenError(
                    "Entferne zuerst alle Unterplätze dieses Lagerplatzes."
                )
            uow.locations.remove(location.id)
            uow.commit()

    def preview_batch(self, specification: BatchSpecification) -> BatchPreview:
        drafts = specification.drafts()
        items: list[BatchPreviewItem] = []
        seen: set[str] = set()
        with self._uow_factory() as uow:
            self._validate_type_and_parent(
                uow, specification.location_type_id, specification.parent_id
            )
            for draft in drafts:
                normalized_code = normalize_location_code(draft.code)
                conflict: str | None = None
                if normalized_code in seen:
                    conflict = "Das Muster erzeugt diese Kennung mehrfach."
                elif uow.locations.find_sibling(
                    specification.parent_id, normalized_code
                ):
                    conflict = (
                        "Diese Kennung ist unter dem Lagerplatz bereits vorhanden."
                    )
                seen.add(normalized_code)
                items.append(BatchPreviewItem(draft, normalized_code, conflict))
        return BatchPreview(specification, tuple(items))

    def create_batch(self, specification: BatchSpecification) -> list[LocationDetails]:
        drafts = specification.drafts()
        created_ids: list[UUID] = []
        with self._uow_factory() as uow:
            self._validate_type_and_parent(
                uow, specification.location_type_id, specification.parent_id
            )
            compartment_type = None
            if specification.split_into_compartments:
                compartment_type = self._require_type(
                    uow.locations.get_type_by_code("compartment")
                )
                if not compartment_type.is_active:
                    raise LocationTypeNotFoundError(
                        "Der Lagerplatztyp Unterfach ist deaktiviert."
                    )
            normalized_codes = [normalize_location_code(draft.code) for draft in drafts]
            if len(set(normalized_codes)) != len(normalized_codes):
                raise BatchConflictError(
                    "Das Muster erzeugt doppelte Kennungen. Es wurde nichts angelegt."
                )
            conflicts = [
                draft.code
                for draft, normalized_code in zip(drafts, normalized_codes, strict=True)
                if uow.locations.find_sibling(specification.parent_id, normalized_code)
            ]
            if conflicts:
                preview = ", ".join(conflicts[:5])
                suffix = " …" if len(conflicts) > 5 else ""
                raise BatchConflictError(
                    f"Bereits vorhandene Kennungen: {preview}{suffix}. "
                    "Es wurde nichts angelegt."
                )
            now = datetime.now(UTC)
            for draft, normalized_code in zip(drafts, normalized_codes, strict=True):
                location = Location(
                    id=uuid4(),
                    code=draft.code,
                    normalized_code=normalized_code,
                    name=draft.name,
                    location_type_id=draft.location_type_id,
                    parent_id=draft.parent_id,
                    description=None,
                    is_active=True,
                    qr_token=self._new_qr_token(uow),
                    created_at=now,
                    updated_at=now,
                )
                uow.locations.add(location)
                created_ids.append(location.id)
                if compartment_type is not None:
                    for compartment_code in ("A", "B"):
                        compartment = Location(
                            id=uuid4(),
                            code=compartment_code,
                            normalized_code=normalize_location_code(compartment_code),
                            name=f"Unterfach {compartment_code}",
                            location_type_id=compartment_type.id,
                            parent_id=location.id,
                            description=None,
                            is_active=True,
                            qr_token=self._new_qr_token(uow),
                            created_at=now,
                            updated_at=now,
                        )
                        uow.locations.add(compartment)
                        created_ids.append(compartment.id)
            uow.commit()
        return [self.get(location_id) for location_id in created_ids]

    def render_qr_svg(self, location_id: UUID, base_url: str) -> bytes:
        details = self.get(location_id)
        renderer = self._require_renderer()
        return renderer.render_qr_svg(self._qr_url(details.location, base_url))

    def render_single_label(self, location_id: UUID, base_url: str) -> bytes:
        details = self.get(location_id)
        return self._require_renderer().render_single(
            self._label_data(details, base_url)
        )

    def render_compact_label(self, location_id: UUID, base_url: str) -> bytes:
        details = self.get(location_id)
        return self._require_renderer().render_compact(
            self._label_data(details, base_url)
        )

    def render_label_sheet(
        self,
        location_ids: list[UUID],
        base_url: str,
        layout: LabelSheetLayout,
    ) -> bytes:
        if not location_ids:
            raise ValidationError("Wähle mindestens einen Lagerplatz aus.")
        if len(location_ids) > 500:
            raise ValidationError("Pro PDF sind höchstens 500 Etiketten möglich.")
        labels = [
            self._label_data(self.get(location_id), base_url)
            for location_id in location_ids
        ]
        return self._require_renderer().render_sheet(labels, layout)

    @staticmethod
    def _clean_draft(draft: LocationDraft) -> tuple[str, str, str, str | None]:
        code = clean_required_text(draft.code, "Kennung", 64)
        return (
            code,
            normalize_location_code(code),
            clean_required_text(draft.name, "Bezeichnung", 120),
            clean_description(draft.description),
        )

    @staticmethod
    def _require_location(
        location: Location | None,
        message: str = "Der Lagerplatz wurde nicht gefunden.",
    ) -> Location:
        if location is None:
            raise LocationNotFoundError(message)
        return location

    @staticmethod
    def _require_type(location_type: LocationType | None) -> LocationType:
        if location_type is None:
            raise LocationTypeNotFoundError("Der Lagerplatztyp wurde nicht gefunden.")
        return location_type

    def _validate_type_and_parent(
        self, uow, location_type_id: UUID, parent_id: UUID | None
    ) -> None:
        location_type = self._require_type(uow.locations.get_type(location_type_id))
        if not location_type.is_active:
            raise LocationTypeNotFoundError("Der Lagerplatztyp ist deaktiviert.")
        if parent_id is not None:
            parent = self._require_location(uow.locations.get(parent_id))
            if not parent.is_active:
                raise InactiveLocationError(
                    "Unter einem deaktivierten Lagerplatz kann nichts angelegt werden."
                )

    @staticmethod
    def _ensure_unique(
        uow,
        parent_id: UUID | None,
        normalized_code: str,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        if uow.locations.find_sibling(
            parent_id, normalized_code, exclude_id=exclude_id
        ):
            raise DuplicateLocationCodeError(
                "Diese Kennung ist unter demselben Lagerplatz bereits vorhanden."
            )

    def _ensure_not_cycle(self, uow, location_id: UUID, parent_id: UUID | None) -> None:
        if parent_id is None:
            return
        if parent_id == location_id:
            raise LocationCycleError("Ein Lagerplatz kann nicht sich selbst enthalten.")
        current_id: UUID | None = parent_id
        visited: set[UUID] = set()
        while current_id is not None:
            if current_id == location_id:
                raise LocationCycleError(
                    "Der Lagerplatz kann nicht unter einen eigenen Unterplatz verschoben werden."
                )
            if current_id in visited:
                raise LocationCycleError(
                    "Die vorhandene Lagerstruktur enthält einen Zyklus."
                )
            visited.add(current_id)
            current = self._require_location(uow.locations.get(current_id))
            current_id = current.parent_id

    @staticmethod
    def _ensure_can_deactivate(uow, location_id: UUID) -> None:
        active_children = [
            child
            for child in uow.locations.list_children(
                location_id, include_inactive=False
            )
            if child.is_active
        ]
        if active_children:
            raise ActiveChildrenError(
                "Der Lagerplatz besitzt aktive Unterplätze. "
                "Deaktiviere oder verschiebe sie zuerst."
            )

    @staticmethod
    def _new_qr_token(uow) -> str:
        for _ in range(5):
            token = secrets.token_urlsafe(18)
            if uow.locations.get_by_qr_token(token) is None:
                return token
        raise RuntimeError("Es konnte kein eindeutiger QR-Token erzeugt werden.")

    @staticmethod
    def _load_path(uow, location: Location) -> tuple[Location, ...]:
        path = [location]
        current = location
        visited = {location.id}
        while current.parent_id is not None:
            parent = LocationService._require_location(
                uow.locations.get(current.parent_id)
            )
            if parent.id in visited:
                raise LocationCycleError("Die Lagerstruktur enthält einen Zyklus.")
            visited.add(parent.id)
            path.append(parent)
            current = parent
        path.reverse()
        return tuple(path)

    @staticmethod
    def _path_from_map(
        location: Location, by_id: dict[UUID, Location]
    ) -> tuple[Location, ...]:
        path = [location]
        current = location
        visited = {location.id}
        while current.parent_id is not None and current.parent_id in by_id:
            current = by_id[current.parent_id]
            if current.id in visited:
                raise LocationCycleError("Die Lagerstruktur enthält einen Zyklus.")
            visited.add(current.id)
            path.append(current)
        path.reverse()
        return tuple(path)

    @staticmethod
    def _qr_url(location: Location, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/q/l/v1/{location.qr_token}"

    def _label_data(self, details: LocationDetails, base_url: str) -> LabelData:
        return LabelData(
            code=details.location.code,
            name=details.location.name,
            path=" / ".join(item.code for item in details.path),
            qr_url=self._qr_url(details.location, base_url),
            qr_short_code=details.location.qr_short_code,
        )

    def _require_renderer(self) -> LabelRenderer:
        if self._label_renderer is None:
            raise RuntimeError("Kein Etiketten-Renderer konfiguriert.")
        return self._label_renderer
