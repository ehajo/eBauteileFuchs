"""Add location hierarchy and built-in location types.

Revision ID: 0002_m1_locations
Revises: 0001_m0_baseline
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_m1_locations"
down_revision: str | None = "0001_m0_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LOCATION_TYPES = (
    ("10000000-0000-4000-8000-000000000001", "room", "Raum", 10),
    ("10000000-0000-4000-8000-000000000002", "cabinet", "Schrank", 20),
    ("10000000-0000-4000-8000-000000000003", "shelf", "Regal", 30),
    ("10000000-0000-4000-8000-000000000004", "magazine", "Magazin", 40),
    ("10000000-0000-4000-8000-000000000005", "drawer", "Schublade", 50),
    ("10000000-0000-4000-8000-000000000006", "compartment", "Unterfach", 60),
    ("10000000-0000-4000-8000-000000000007", "box", "Box", 70),
    ("10000000-0000-4000-8000-000000000008", "crate", "Kiste", 80),
)


def upgrade() -> None:
    location_type = op.create_table(
        "location_type",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_location_type_code"),
    )
    op.bulk_insert(
        location_type,
        [
            {
                "id": identifier,
                "code": code,
                "name": name,
                "sort_order": sort_order,
                "is_system": True,
                "is_active": True,
            }
            for identifier, code, name, sort_order in LOCATION_TYPES
        ],
    )

    op.create_table(
        "location",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("normalized_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("location_type_id", sa.String(length=36), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("parent_scope", sa.String(length=36), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("qr_token", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "parent_scope = COALESCE(parent_id, '__root__')",
            name="ck_location_parent_scope",
        ),
        sa.ForeignKeyConstraint(
            ["location_type_id"], ["location_type.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["location.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "parent_scope",
            "normalized_code",
            name="uq_location_parent_scope_normalized_code",
        ),
        sa.UniqueConstraint("qr_token", name="uq_location_qr_token"),
    )
    op.create_index("ix_location_location_type_id", "location", ["location_type_id"])
    op.create_index("ix_location_parent_id", "location", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_location_parent_id", table_name="location")
    op.drop_index("ix_location_location_type_id", table_name="location")
    op.drop_table("location")
    op.drop_table("location_type")
