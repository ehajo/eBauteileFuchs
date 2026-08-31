import pytest

from ebauteilefuchs.application.connection import (
    build_connection_overview,
    validate_connection_url,
)
from ebauteilefuchs.domain.errors import ValidationError
from ebauteilefuchs.platform.network import NetworkAddress


def test_connection_overview_prefers_configured_or_private_address() -> None:
    addresses = (
        NetworkAddress("192.168.1.42", True),
        NetworkAddress("10.0.0.5", True),
    )
    detected = build_connection_overview(
        hostname="synthetic-pc",
        port=8008,
        local_url="http://127.0.0.1:8008",
        addresses=addresses,
    )
    assert detected.selected_url == "http://192.168.1.42:8008"
    assert detected.choices[0].recommended is True

    configured = build_connection_overview(
        hostname="synthetic-pc",
        port=8008,
        local_url="http://127.0.0.1:8008",
        addresses=addresses,
        configured_url="http://partsbox.local:8008",
    )
    assert configured.selected_url == "http://partsbox.local:8008"
    assert configured.choices[0].label == "Konfigurierte Basis-URL"

    secure = build_connection_overview(
        hostname="synthetic-pc",
        port=8008,
        local_url="https://127.0.0.1:8008",
        addresses=addresses,
        scheme="https",
    )
    assert secure.selected_url == "https://192.168.1.42:8008"


@pytest.mark.parametrize(
    "value",
    (
        "javascript:alert(1)",
        "http://user:secret@localhost:8008",
        "http://localhost:8008/redirect",
        "http://localhost:8008?next=https://example.invalid",
    ),
)
def test_connection_url_rejects_unsafe_values(value: str) -> None:
    with pytest.raises(ValidationError):
        validate_connection_url(value)
