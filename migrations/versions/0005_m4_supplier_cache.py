"""Add the generic M4 supplier cache schema.

Revision ID: 0005_m4_supplier_cache
Revises: 0004_m3_inventory
Create Date: 2026-08-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_m4_supplier_cache"
down_revision: str | None = "0004_m3_inventory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "supplier_cache_entry",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("supplier_id", sa.String(36), nullable=False),
        sa.Column("query_type", sa.String(40), nullable=False),
        sa.Column("query_normalized", sa.String(160), nullable=False),
        sa.Column("adapter_version", sa.String(40), nullable=False),
        sa.Column("response_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "supplier_id",
            "query_type",
            "query_normalized",
            "adapter_version",
            name="uq_supplier_cache_lookup",
        ),
    )
    op.create_index(
        "ix_supplier_cache_expires_at", "supplier_cache_entry", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_supplier_cache_expires_at", table_name="supplier_cache_entry")
    op.drop_table("supplier_cache_entry")
