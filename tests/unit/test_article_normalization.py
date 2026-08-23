import pytest

from ebauteilefuchs.domain.articles import (
    normalize_manufacturer_name,
    normalize_part_number,
    normalize_search_text,
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("  Texas   Instruments ", "texas instruments"),
        ("VISHAY", "vishay"),
        ("MuRata", "murata"),
    ],
)
def test_manufacturer_normalization(source: str, expected: str) -> None:
    assert normalize_manufacturer_name(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (" CRCW0805-10K0-FKEA ", "CRCW080510K0FKEA"),
        ("crcw 0805 / 10k0_fkea", "CRCW080510K0FKEA"),
        ("NE555P", "NE555P"),
        ("GRM21BR71H104KA01L", "GRM21BR71H104KA01L"),
    ],
)
def test_part_number_normalization(source: str, expected: str) -> None:
    assert normalize_part_number(source) == expected


def test_search_normalization_keeps_engineering_terms() -> None:
    assert normalize_search_text(" 10 kΩ, 0805 / 1 % ") == "10 kω 0805 1"
