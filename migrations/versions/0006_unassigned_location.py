"""Add the history-safe internal unassigned storage location.

Revision ID: 0006_unassigned_location
Revises: 0005_m4_supplier_cache
"""

from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision = "0006_unassigned_location"
down_revision = "0005_m4_supplier_cache"
branch_labels = None
depends_on = None

LOCATION_ID = "10000000-0000-4000-8000-000000000099"


def upgrade() -> None:
    location = sa.table(
        "location",
        sa.column("id", sa.String),
        sa.column("code", sa.String),
        sa.column("normalized_code", sa.String),
        sa.column("name", sa.String),
        sa.column("location_type_id", sa.String),
        sa.column("parent_id", sa.String),
        sa.column("parent_scope", sa.String),
        sa.column("description", sa.Text),
        sa.column("is_active", sa.Boolean),
        sa.column("qr_token", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(UTC)
    op.bulk_insert(
        location,
        [
            {
                "id": LOCATION_ID,
                "code": "OHNE-LAGERPLATZ",
                "normalized_code": "ohne-lagerplatz",
                "name": "Ohne Lagerplatz",
                "location_type_id": "10000000-0000-4000-8000-000000000008",
                "parent_id": None,
                "parent_scope": "__root__",
                "description": "Interner Sammelplatz für archivierte Lagerbereiche.",
                "is_active": True,
                "qr_token": "internal-unassigned-v1",
                "created_at": now,
                "updated_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM location WHERE id = :location_id").bindparams(
            location_id=LOCATION_ID
        )
    )
