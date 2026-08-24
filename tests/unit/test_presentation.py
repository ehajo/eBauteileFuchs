from decimal import Decimal

from ebauteilefuchs.web.presentation import format_decimal, unit_choices


def test_decimal_formatting_avoids_scientific_notation() -> None:
    assert format_decimal(Decimal("1E+2")) == "100"
    assert format_decimal(Decimal("12.50000000")) == "12.5"
    assert format_decimal(Decimal("0E-8")) == "0"


def test_unit_choices_offer_practical_engineering_prefixes() -> None:
    assert unit_choices("F") == ("pF", "nF", "µF", "mF", "F")
    assert unit_choices("Ω") == ("mΩ", "Ω", "kΩ", "MΩ", "GΩ")
