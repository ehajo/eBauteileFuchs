"""Build and validate local connection choices without persisting network state."""

from dataclasses import dataclass
from urllib.parse import urlsplit

from ebauteilefuchs.domain.errors import ValidationError
from ebauteilefuchs.platform.network import NetworkAddress


@dataclass(frozen=True, slots=True)
class ConnectionChoice:
    label: str
    url: str
    recommended: bool = False


@dataclass(frozen=True, slots=True)
class ConnectionOverview:
    hostname: str
    local_url: str
    choices: tuple[ConnectionChoice, ...]
    selected_url: str


def build_connection_overview(
    *,
    hostname: str,
    port: int,
    local_url: str,
    addresses: tuple[NetworkAddress, ...],
    configured_url: str | None = None,
    selected_url: str | None = None,
    scheme: str = "http",
) -> ConnectionOverview:
    choices: list[ConnectionChoice] = []
    if configured_url:
        choices.append(
            ConnectionChoice("Konfigurierte Basis-URL", configured_url, True)
        )
    for index, address in enumerate(addresses):
        url = f"{scheme}://{address.address}:{port}"
        choices.append(
            ConnectionChoice(
                f"Lokale IPv4-Adresse {address.address}",
                url,
                recommended=not choices and index == 0,
            )
        )
    fallback = configured_url or (choices[0].url if choices else local_url)
    selected = validate_connection_url(selected_url) if selected_url else fallback
    if all(choice.url != selected for choice in choices):
        choices.append(ConnectionChoice("Manuell eingegebene Adresse", selected))
    return ConnectionOverview(hostname, local_url, tuple(choices), selected)


def validate_connection_url(value: str) -> str:
    cleaned = value.strip().rstrip("/")
    if len(cleaned) > 500:
        raise ValidationError("Die Verbindungsadresse ist zu lang.")
    parsed = urlsplit(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError(
            "Die Verbindungsadresse muss eine vollständige HTTP- oder HTTPS-Adresse sein."
        )
    if parsed.username or parsed.password:
        raise ValidationError(
            "Die Verbindungsadresse darf keine Zugangsdaten enthalten."
        )
    if parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise ValidationError(
            "Die Verbindungsadresse darf keinen Pfad oder Zusatz enthalten."
        )
    return cleaned
