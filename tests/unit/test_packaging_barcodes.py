import pytest

from ebauteilefuchs.application.supplier_search import SupplierSearchService
from ebauteilefuchs.domain.barcodes import parse_packaging_barcode
from ebauteilefuchs.domain.errors import ValidationError
from ebauteilefuchs.domain.suppliers import SupplierSearchMode


class EmptyArticles:
    def find_by_supplier_number(self, supplier_code: str, number: str):
        return None

    def list_articles(self, *, query: str, include_inactive: bool):
        return []


class RecordingAdapter:
    configured = True

    def __init__(self) -> None:
        self.query = None
        self.mode = None

    def search(self, query: str, mode: SupplierSearchMode):
        self.query = query
        self.mode = mode
        return ()


def test_wurth_data_identifiers_are_interpreted() -> None:
    parsed = parse_packaging_barcode(
        "]d2[)>\x1e06\x1d1P74404084100\x1d1TLOT-240824\x1dQ500\x1e\x04"
    )

    assert parsed.product_codes == ("74404084100",)
    assert parsed.lot_numbers == ("LOT-240824",)
    assert parsed.quantities == ("500",)


def test_displayed_group_separators_are_supported() -> None:
    parsed = parse_packaging_barcode("1P74404084100<GS>1TLOT-42<GS>Q100")

    assert parsed.product_codes == ("74404084100",)
    assert parsed.lot_numbers == ("LOT-42",)
    assert parsed.quantities == ("100",)


def test_barcode_search_uses_only_wurth_product_code() -> None:
    adapter = RecordingAdapter()
    service = SupplierSearchService(EmptyArticles(), adapter)

    result = service.search("1P74404084100", SupplierSearchMode.BARCODE)

    assert result.query == "74404084100"
    assert adapter.query == "74404084100"
    assert adapter.mode is SupplierSearchMode.BARCODE


@pytest.mark.parametrize("query", ["1TLOT-240824", "Q500"])
def test_lot_or_quantity_cannot_be_searched_as_product(query: str) -> None:
    service = SupplierSearchService(EmptyArticles(), RecordingAdapter())

    with pytest.raises(ValidationError, match="Würth-Produktcode"):
        service.search(query, SupplierSearchMode.BARCODE)
