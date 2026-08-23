"""Stable M2 seed data for categories, attributes, and suppliers."""

from uuid import UUID

CATEGORIES = (
    (UUID("20000000-0000-4000-8000-000000000001"), "resistor", "Widerstand", 10),
    (UUID("20000000-0000-4000-8000-000000000002"), "capacitor", "Kondensator", 20),
    (UUID("20000000-0000-4000-8000-000000000003"), "inductor", "Induktivität", 30),
    (UUID("20000000-0000-4000-8000-000000000004"), "diode", "Diode", 40),
    (
        UUID("20000000-0000-4000-8000-000000000005"),
        "transistor_mosfet",
        "Transistor / MOSFET",
        50,
    ),
    (
        UUID("20000000-0000-4000-8000-000000000006"),
        "integrated_circuit",
        "Integrierter Schaltkreis",
        60,
    ),
    (UUID("20000000-0000-4000-8000-000000000007"), "led", "LED", 70),
    (UUID("20000000-0000-4000-8000-000000000008"), "connector", "Steckverbinder", 80),
    (
        UUID("20000000-0000-4000-8000-000000000009"),
        "mechanical",
        "Mechanisches Bauteil",
        90,
    ),
    (UUID("20000000-0000-4000-8000-000000000010"), "other", "Sonstiges", 100),
)

ATTRIBUTE_DEFINITIONS = (
    ("resistance", "Widerstandswert", "text", "Ω"),
    ("tolerance", "Toleranz", "text", "%"),
    ("power", "Leistung", "text", "W"),
    ("package", "Bauform / Gehäuse", "text", None),
    ("temperature_coefficient", "Temperaturkoeffizient", "text", "ppm/K"),
    ("capacitance", "Kapazität", "text", "F"),
    ("rated_voltage", "Nennspannung", "text", "V"),
    ("dielectric", "Dielektrikum", "text", None),
    ("inductance", "Induktivität", "text", "H"),
    ("rated_current", "Nennstrom", "text", "A"),
    ("dc_resistance", "Gleichstromwiderstand", "text", "Ω"),
    ("diode_type", "Diodentyp", "text", None),
    ("reverse_voltage", "Sperrspannung", "text", "V"),
    ("current", "Strom", "text", "A"),
    ("technology", "Technologie", "text", None),
    ("voltage", "Spannung", "text", "V"),
    ("power_dissipation", "Verlustleistung", "text", "W"),
    ("function", "Funktion", "text", None),
    ("pin_count", "Pinzahl", "integer", None),
    ("supply_voltage", "Versorgungsspannung", "text", "V"),
    ("color", "Farbe", "text", None),
    ("wavelength", "Wellenlänge", "text", "nm"),
    ("forward_voltage", "Durchlassspannung", "text", "V"),
    ("series", "Serie", "text", None),
    ("pole_count", "Polzahl", "integer", None),
    ("pitch", "Raster", "text", "mm"),
    ("gender", "Geschlecht", "text", None),
    ("mounting_type", "Montageart", "text", None),
    ("dimensions", "Abmessungen", "text", None),
    ("material", "Material", "text", None),
    ("thread", "Gewinde", "text", None),
    ("variant", "Ausführung", "text", None),
)

ATTRIBUTE_IDS = {
    code: UUID(f"30000000-0000-4000-8000-{index:012d}")
    for index, (code, *_rest) in enumerate(ATTRIBUTE_DEFINITIONS, start=1)
}

CATEGORY_ATTRIBUTE_CODES = {
    "resistor": (
        "resistance",
        "tolerance",
        "power",
        "package",
        "temperature_coefficient",
    ),
    "capacitor": (
        "capacitance",
        "rated_voltage",
        "tolerance",
        "dielectric",
        "package",
    ),
    "inductor": ("inductance", "rated_current", "dc_resistance", "package"),
    "diode": ("diode_type", "reverse_voltage", "current", "package"),
    "transistor_mosfet": (
        "technology",
        "voltage",
        "current",
        "power_dissipation",
        "package",
    ),
    "integrated_circuit": ("function", "package", "pin_count", "supply_voltage"),
    "led": ("color", "wavelength", "forward_voltage", "current", "package"),
    "connector": ("series", "pole_count", "pitch", "gender", "mounting_type"),
    "mechanical": ("dimensions", "material", "thread", "variant"),
    "other": (),
}

MOUSER_SUPPLIER = (
    UUID("40000000-0000-4000-8000-000000000001"),
    "mouser",
    "Mouser Electronics",
    "mouser",
)
