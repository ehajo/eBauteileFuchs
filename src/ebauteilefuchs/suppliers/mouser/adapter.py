"""Official Mouser Search API implementation of the neutral supplier port."""

from ebauteilefuchs.domain.errors import SupplierNotConfiguredError
from ebauteilefuchs.domain.suppliers import SupplierProduct, SupplierSearchMode
from ebauteilefuchs.suppliers.mouser.client import MouserHttpClient
from ebauteilefuchs.suppliers.mouser.mapper import map_part
from ebauteilefuchs.suppliers.mouser.schemas import parse_search_response


class MouserAdapter:
    code = "mouser"

    def __init__(self, api_key: str | None, *, client: MouserHttpClient | None = None):
        self._api_key = (api_key or "").strip()
        self._client = client or (
            MouserHttpClient(self._api_key) if self._api_key else None
        )

    @property
    def configured(self) -> bool:
        return bool(self._api_key and self._client)

    def search(
        self, query: str, mode: SupplierSearchMode
    ) -> tuple[SupplierProduct, ...]:
        cleaned = " ".join(query.split())
        if not self.configured:
            raise SupplierNotConfiguredError(
                "Die Mouser-Suche ist nicht eingerichtet. Hinterlege den API-Schlüssel lokal oder lege den Artikel manuell an."
            )
        if mode == SupplierSearchMode.KEYWORD:
            endpoint = "keyword"
            body = {
                "SearchByKeywordRequest": {
                    "keyword": cleaned,
                    "records": 0,
                    "startingRecord": 0,
                    "searchOptions": "None",
                    "searchWithYourSignUpLanguage": "None",
                }
            }
        else:
            endpoint = "partnumber"
            body = {
                "SearchByPartRequest": {
                    "mouserPartNumber": cleaned,
                    "partSearchOptions": "None",
                }
            }
        payload = self._client.search(endpoint, body)
        return tuple(map_part(part) for part in parse_search_response(payload))
