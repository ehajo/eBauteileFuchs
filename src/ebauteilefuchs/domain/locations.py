"""Location entities and hierarchy-independent validation rules."""

import re
import string
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ebauteilefuchs.domain.errors import ValidationError

WHITESPACE = re.compile(r"\s+")
ALLOWED_PATTERN_FIELDS = {"number", "number_padded", "index"}
UNASSIGNED_LOCATION_ID = UUID("10000000-0000-4000-8000-000000000099")


def normalize_location_code(value: str) -> str:
    """Normalize a code for sibling uniqueness without changing its display form."""

    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    return WHITESPACE.sub(" ", normalized)


def clean_required_text(value: str, field_name: str, max_length: int) -> str:
    cleaned = WHITESPACE.sub(" ", unicodedata.normalize("NFKC", value).strip())
    if not cleaned:
        raise ValidationError(f"{field_name} darf nicht leer sein.")
    if len(cleaned) > max_length:
        raise ValidationError(
            f"{field_name} darf höchstens {max_length} Zeichen enthalten."
        )
    return cleaned


def clean_description(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = unicodedata.normalize("NFKC", value).strip()
    if not cleaned:
        return None
    if len(cleaned) > 1_000:
        raise ValidationError("Die Beschreibung darf höchstens 1000 Zeichen enthalten.")
    return cleaned


@dataclass(frozen=True, slots=True)
class LocationType:
    id: UUID
    code: str
    name: str
    sort_order: int
    is_system: bool
    is_active: bool


@dataclass(frozen=True, slots=True)
class Location:
    id: UUID
    code: str
    normalized_code: str
    name: str
    location_type_id: UUID
    parent_id: UUID | None
    description: str | None
    is_active: bool
    qr_token: str
    created_at: datetime
    updated_at: datetime

    @property
    def qr_short_code(self) -> str:
        return f"L-{self.qr_token[:8].upper()}"


@dataclass(frozen=True, slots=True)
class LocationDraft:
    code: str
    name: str
    location_type_id: UUID
    parent_id: UUID | None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class BatchSpecification:
    parent_id: UUID
    location_type_id: UUID
    count: int = 60
    start_number: int = 1
    padding: int = 2
    code_pattern: str = "{number_padded}"
    name_pattern: str = "Schublade {number_padded}"
    split_into_compartments: bool = False
    magazine_code: str | None = None
    magazine_name: str | None = None

    def validate(self) -> None:
        if not 1 <= self.count <= 200:
            raise ValidationError("Die Anzahl muss zwischen 1 und 200 liegen.")
        if not 0 <= self.start_number <= 999_999:
            raise ValidationError("Die Startnummer muss zwischen 0 und 999999 liegen.")
        if not 1 <= self.padding <= 6:
            raise ValidationError("Die Stellenzahl muss zwischen 1 und 6 liegen.")
        self._validate_pattern(self.code_pattern, "Kennungsmuster")
        self._validate_pattern(self.name_pattern, "Namensmuster")
        if (self.magazine_code is None) != (self.magazine_name is None):
            raise ValidationError(
                "Kennung und Bezeichnung des Magazins müssen gemeinsam angegeben werden."
            )
        if self.magazine_code is not None:
            clean_required_text(self.magazine_code, "Magazinkennung", 64)
            clean_required_text(self.magazine_name or "", "Magazinbezeichnung", 120)

    @staticmethod
    def _validate_pattern(pattern: str, field_name: str) -> None:
        if not pattern or len(pattern) > 120:
            raise ValidationError(f"{field_name} muss 1 bis 120 Zeichen enthalten.")
        try:
            parsed = string.Formatter().parse(pattern)
            for _, field, format_spec, conversion in parsed:
                if field is None:
                    continue
                if field not in ALLOWED_PATTERN_FIELDS:
                    allowed = ", ".join(sorted(ALLOWED_PATTERN_FIELDS))
                    raise ValidationError(
                        f"{field_name} enthält {{{field}}}. Erlaubt sind: {allowed}."
                    )
                if format_spec or conversion:
                    raise ValidationError(
                        f"{field_name} darf keine Format- oder Konvertierungsangaben enthalten."
                    )
        except ValueError as error:
            raise ValidationError(
                f"{field_name} enthält ungültige Klammern."
            ) from error

    def drafts(self) -> list[LocationDraft]:
        self.validate()
        items: list[LocationDraft] = []
        for index in range(self.count):
            number = self.start_number + index
            values = {
                "number": str(number),
                "number_padded": str(number).zfill(self.padding),
                "index": str(index + 1),
            }
            code = clean_required_text(
                self.code_pattern.format_map(values), "Kennung", 64
            )
            name = clean_required_text(
                self.name_pattern.format_map(values), "Bezeichnung", 120
            )
            items.append(
                LocationDraft(
                    code=code,
                    name=name,
                    location_type_id=self.location_type_id,
                    parent_id=self.parent_id,
                )
            )
        return items
