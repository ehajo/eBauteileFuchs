"""Retain the already deployed article-barcode schema revision.

The application no longer stores packaging barcodes on articles. This revision
must remain available because development databases may already be stamped with
its identifier. The table is kept for migration compatibility and is unused.

Revision ID: 0007_article_barcodes
Revises: 0006_unassigned_location
"""

import sqlalchemy as sa
from alembic import op

revision = "0007_article_barcodes"
down_revision = "0006_unassigned_location"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "article_barcode",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("article_id", sa.String(length=36), nullable=False),
        sa.Column("value", sa.String(length=200), nullable=False),
        sa.Column("normalized_value", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["article.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "normalized_value", name="uq_article_barcode_normalized_value"
        ),
    )
    op.create_index("ix_article_barcode_article_id", "article_barcode", ["article_id"])


def downgrade() -> None:
    op.drop_index("ix_article_barcode_article_id", table_name="article_barcode")
    op.drop_table("article_barcode")
