"""Bounded HTTP transport for the official Mouser Search API."""

import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ebauteilefuchs.domain.errors import (
    SupplierAuthenticationError,
    SupplierRateLimitError,
    SupplierResponseError,
    SupplierUnavailableError,
)

MAX_RESPONSE_BYTES = 2_000_000


class MouserHttpClient:
    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float = 8.0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._opener = opener

    def search(self, endpoint: str, body: dict) -> dict:
        url = f"https://api.mouser.com/api/v1/search/{endpoint}?" + urlencode(
            {"apiKey": self._api_key}
        )
        request = Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        content = b""
        for attempt in range(2):
            try:
                with self._opener(request, timeout=self._timeout) as response:
                    content = response.read(MAX_RESPONSE_BYTES + 1)
                break
            except HTTPError as error:
                if error.code in {401, 403}:
                    raise SupplierAuthenticationError(
                        "Der Mouser-API-Schlüssel wurde abgelehnt. Prüfe die lokale Konfiguration."
                    ) from None
                if error.code == 429:
                    raise SupplierRateLimitError(
                        "Das Mouser-Anfragelimit ist erreicht. Bitte versuche es später erneut."
                    ) from None
                if attempt == 0 and error.code >= 500:
                    continue
                raise SupplierUnavailableError(
                    f"Mouser ist derzeit nicht erreichbar (HTTP {error.code})."
                ) from None
            except TimeoutError:
                if attempt == 0:
                    continue
                raise SupplierUnavailableError(
                    "Die Mouser-Anfrage hat zu lange gedauert. Bitte versuche es erneut."
                ) from None
            except URLError:
                if attempt == 0:
                    continue
                raise SupplierUnavailableError(
                    "Mouser konnte über das Netzwerk nicht erreicht werden. Prüfe die Internetverbindung."
                ) from None
        if len(content) > MAX_RESPONSE_BYTES:
            raise SupplierResponseError("Die Mouser-Antwort ist unerwartet groß.")
        try:
            payload = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise SupplierResponseError(
                "Mouser hat keine gültige JSON-Antwort geliefert."
            ) from None
        if not isinstance(payload, dict):
            raise SupplierResponseError(
                "Mouser hat eine unerwartete Antwort geliefert."
            )
        return payload
