from decimal import Decimal

import pytest

from ebauteilefuchs.domain.errors import ValidationError
from ebauteilefuchs.domain.inventory import parse_quantity, positive_quantity


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1", Decimal("1")), ("12,5", Decimal("12.5")), ("0.00000001", Decimal("1E-8"))],
)
def test_decimal_quantity_is_parsed_without_binary_float(value, expected) -> None:
    assert parse_quantity(value) == expected


@pytest.mark.parametrize("value", ["NaN", "Infinity", "1.000000001", "abc", 1.2])
def test_invalid_quantities_are_rejected(value) -> None:
    with pytest.raises(ValidationError):
        parse_quantity(value)


def test_positive_quantity_rejects_zero_and_negative_values() -> None:
    with pytest.raises(ValidationError):
        positive_quantity("0")
    with pytest.raises(ValidationError):
        positive_quantity("-1")
