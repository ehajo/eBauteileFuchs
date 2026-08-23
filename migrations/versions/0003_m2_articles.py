"""Add M2 article catalog, properties, and supplier identifiers.

Revision ID: 0003_m2_articles
Revises: 0002_m1_locations
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_m2_articles"
down_revision: str | None = "0002_m1_locations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CATEGORIES = (
    (1, "resistor", "Widerstand", 10),
    (2, "capacitor", "Kondensator", 20),
    (3, "inductor", "Induktivität", 30),
    (4, "diode", "Diode", 40),
    (5, "transistor_mosfet", "Transistor / MOSFET", 50),
    (6, "integrated_circuit", "Integrierter Schaltkreis", 60),
    (7, "led", "LED", 70),
    (8, "connector", "Steckverbinder", 80),
    (9, "mechanical", "Mechanisches Bauteil", 90),
    (10, "other", "Sonstiges", 100),
)

ATTRIBUTES = (
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

CATEGORY_ATTRIBUTES = {
    "resistor": (
        "resistance",
        "tolerance",
        "power",
        "package",
        "temperature_coefficient",
    ),
    "capacitor": ("capacitance", "rated_voltage", "tolerance", "dielectric", "package"),
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


def category_id(index: int) -> str:
    return f"20000000-0000-4000-8000-{index:012d}"


def attribute_id(index: int) -> str:
    return f"30000000-0000-4000-8000-{index:012d}"


def upgrade() -> None:
    op.create_table(
        "manufacturer",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("normalized_name", sa.String(120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("normalized_name", name="uq_manufacturer_normalized_name"),
    )
    op.create_index(
        "ix_manufacturer_normalized_name", "manufacturer", ["normalized_name"]
    )

    category = op.create_table(
        "category",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.UniqueConstraint("code", name="uq_category_code"),
    )
    op.bulk_insert(
        category,
        [
            {
                "id": category_id(index),
                "code": code,
                "name": name,
                "description": None,
                "is_system": True,
                "is_active": True,
                "sort_order": order,
            }
            for index, code, name, order in CATEGORIES
        ],
    )

    supplier = op.create_table(
        "supplier",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("adapter_name", sa.String(80), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("code", name="uq_supplier_code"),
    )
    op.bulk_insert(
        supplier,
        [
            {
                "id": "40000000-0000-4000-8000-000000000001",
                "code": "mouser",
                "name": "Mouser Electronics",
                "adapter_name": "mouser",
                "is_system": True,
                "is_active": True,
            }
        ],
    )

    attribute_definition = op.create_table(
        "attribute_definition",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("value_kind", sa.String(16), nullable=False),
        sa.Column("canonical_unit", sa.String(24), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("code", name="uq_attribute_definition_code"),
    )
    op.bulk_insert(
        attribute_definition,
        [
            {
                "id": attribute_id(index),
                "code": code,
                "name": name,
                "value_kind": value_kind,
                "canonical_unit": unit,
                "is_system": True,
                "is_active": True,
            }
            for index, (code, name, value_kind, unit) in enumerate(ATTRIBUTES, start=1)
        ],
    )

    category_attribute = op.create_table(
        "category_attribute",
        sa.Column("category_id", sa.String(36), nullable=False),
        sa.Column("attribute_definition_id", sa.String(36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_typical", sa.Boolean(), nullable=False),
        sa.Column("allowed_units_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["attribute_definition_id"], ["attribute_definition.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("category_id", "attribute_definition_id"),
    )
    category_ids = {code: category_id(index) for index, code, *_ in CATEGORIES}
    attribute_ids = {
        code: attribute_id(index)
        for index, (code, *_rest) in enumerate(ATTRIBUTES, start=1)
    }
    op.bulk_insert(
        category_attribute,
        [
            {
                "category_id": category_ids[category_code],
                "attribute_definition_id": attribute_ids[attribute_code],
                "sort_order": order,
                "is_typical": True,
                "allowed_units_json": "[]",
            }
            for category_code, attribute_codes in CATEGORY_ATTRIBUTES.items()
            for order, attribute_code in enumerate(attribute_codes, start=10)
        ],
    )

    op.create_table(
        "article",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("manufacturer_id", sa.String(36), nullable=True),
        sa.Column("manufacturer_part_number", sa.String(160), nullable=True),
        sa.Column("normalized_manufacturer_part_number", sa.String(160), nullable=True),
        sa.Column("category_id", sa.String(36), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("datasheet_url", sa.String(500), nullable=True),
        sa.Column("product_url", sa.String(500), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["manufacturer_id"], ["manufacturer.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "manufacturer_id",
            "normalized_manufacturer_part_number",
            name="uq_article_manufacturer_normalized_part_number",
        ),
    )
    op.create_index("ix_article_category_id", "article", ["category_id"])
    op.create_index("ix_article_manufacturer_id", "article", ["manufacturer_id"])
    op.create_index("ix_article_search_text", "article", ["search_text"])
    op.create_index(
        "ix_article_normalized_manufacturer_part_number",
        "article",
        ["normalized_manufacturer_part_number"],
    )

    op.create_table(
        "article_attribute",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("article_id", sa.String(36), nullable=False),
        sa.Column("attribute_definition_id", sa.String(36), nullable=True),
        sa.Column("custom_name", sa.String(100), nullable=True),
        sa.Column("raw_value", sa.String(240), nullable=False),
        sa.Column("normalized_text", sa.String(240), nullable=False),
        sa.Column("numeric_value", sa.Numeric(24, 8), nullable=True),
        sa.Column("unit", sa.String(24), nullable=True),
        sa.Column("canonical_numeric_value", sa.Numeric(24, 8), nullable=True),
        sa.Column("canonical_unit", sa.String(24), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "(attribute_definition_id IS NOT NULL AND custom_name IS NULL) OR "
            "(attribute_definition_id IS NULL AND custom_name IS NOT NULL)",
            name="ck_article_attribute_definition_or_custom",
        ),
        sa.ForeignKeyConstraint(["article_id"], ["article.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["attribute_definition_id"],
            ["attribute_definition.id"],
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_article_attribute_article_id", "article_attribute", ["article_id"]
    )
    op.create_index(
        "ix_article_attribute_normalized_text", "article_attribute", ["normalized_text"]
    )

    op.create_table(
        "supplier_part",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("article_id", sa.String(36), nullable=False),
        sa.Column("supplier_id", sa.String(36), nullable=False),
        sa.Column("supplier_part_number", sa.String(160), nullable=False),
        sa.Column("normalized_supplier_part_number", sa.String(160), nullable=False),
        sa.Column("product_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["article.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "supplier_id",
            "normalized_supplier_part_number",
            name="uq_supplier_part_supplier_normalized_number",
        ),
    )
    op.create_index("ix_supplier_part_article_id", "supplier_part", ["article_id"])
    op.create_index(
        "ix_supplier_part_normalized_supplier_part_number",
        "supplier_part",
        ["normalized_supplier_part_number"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_supplier_part_normalized_supplier_part_number", table_name="supplier_part"
    )
    op.drop_index("ix_supplier_part_article_id", table_name="supplier_part")
    op.drop_table("supplier_part")
    op.drop_index(
        "ix_article_attribute_normalized_text", table_name="article_attribute"
    )
    op.drop_index("ix_article_attribute_article_id", table_name="article_attribute")
    op.drop_table("article_attribute")
    op.drop_index(
        "ix_article_normalized_manufacturer_part_number", table_name="article"
    )
    op.drop_index("ix_article_search_text", table_name="article")
    op.drop_index("ix_article_manufacturer_id", table_name="article")
    op.drop_index("ix_article_category_id", table_name="article")
    op.drop_table("article")
    op.drop_table("category_attribute")
    op.drop_table("attribute_definition")
    op.drop_table("supplier")
    op.drop_table("category")
    op.drop_index("ix_manufacturer_normalized_name", table_name="manufacturer")
    op.drop_table("manufacturer")
