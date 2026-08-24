import json
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from ebauteilefuchs.domain.errors import (
    SupplierAuthenticationError,
    SupplierRateLimitError,
    SupplierResponseError,
    SupplierUnavailableError,
)
from ebauteilefuchs.domain.suppliers import (
    SupplierSearchMode,
    normalize_engineering_value,
)
from ebauteilefuchs.suppliers.mouser import MouserAdapter
from ebauteilefuchs.suppliers.mouser.client import MouserHttpClient

FIXTURES = Path(__file__).parents[1] / "fixtures" / "mouser"


class JsonResponse:
    def __init__(self, payload: object) -> None:
        self.content = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def read(self, limit: int) -> bytes:
        return self.content[:limit]


def test_mouser_mapping_and_unit_normalization() -> None:
    payload = json.loads((FIXTURES / "search_one.json").read_text(encoding="utf-8"))
    client = MouserHttpClient(
        "synthetic-key", opener=lambda *_args, **_kwargs: JsonResponse(payload)
    )
    adapter = MouserAdapter("synthetic-key", client=client)

    products = adapter.search("71-SYNTH-10K", SupplierSearchMode.PART_NUMBER)

    assert len(products) == 1
    assert products[0].suggested_category_code == "resistor"
    resistance = next(
        item for item in products[0].attributes if item.definition_code == "resistance"
    )
    assert (resistance.value, resistance.unit, resistance.original_value) == (
        "10",
        "kΩ",
        "10000 Ohms",
    )
    assert normalize_engineering_value("0.1 uF") == ("100", "nF", True)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            HTTPError("https://example.invalid", 401, "", {}, None),
            SupplierAuthenticationError,
        ),
        (
            HTTPError("https://example.invalid", 429, "", {}, None),
            SupplierRateLimitError,
        ),
        (URLError("offline"), SupplierUnavailableError),
        (TimeoutError(), SupplierUnavailableError),
    ],
)
def test_mouser_http_errors_are_safe(
    error: Exception, expected: type[Exception]
) -> None:
    def failing(*_args, **_kwargs):
        raise error

    with pytest.raises(expected) as caught:
        MouserHttpClient("secret-never-shown", opener=failing).search("keyword", {})
    assert "secret-never-shown" not in str(caught.value)


def test_unexpected_mouser_response_is_rejected() -> None:
    client = MouserHttpClient(
        "synthetic-key",
        opener=lambda *_args, **_kwargs: JsonResponse({"unexpected": []}),
    )
    adapter = MouserAdapter("synthetic-key", client=client)
    with pytest.raises(SupplierResponseError):
        adapter.search("test", SupplierSearchMode.KEYWORD)
