from uuid import uuid4

import pytest

from ebauteilefuchs.domain.errors import ValidationError
from ebauteilefuchs.domain.locations import (
    BatchSpecification,
    normalize_location_code,
)


def test_location_code_normalization_preserves_semantic_characters() -> None:
    assert normalize_location_code("  Fach   Ä-01 ") == "fach ä-01"


def test_batch_specification_rejects_unknown_or_formatted_placeholders() -> None:
    common = {"parent_id": uuid4(), "location_type_id": uuid4()}
    with pytest.raises(ValidationError, match="Erlaubt sind"):
        BatchSpecification(**common, code_pattern="{secret}").drafts()
    with pytest.raises(ValidationError, match="Format"):
        BatchSpecification(**common, code_pattern="{number:03}").drafts()


def test_batch_specification_generates_padded_drafts() -> None:
    specification = BatchSpecification(
        parent_id=uuid4(),
        location_type_id=uuid4(),
        count=3,
        start_number=8,
        padding=2,
    )
    assert [draft.code for draft in specification.drafts()] == ["08", "09", "10"]
