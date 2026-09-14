"""Add optional row and column layout metadata to locations.

Revision ID: 0008_location_grid
Revises: 0007_article_barcodes
"""

import sqlalchemy as sa
from alembic import op

revision = "0008_location_grid"
down_revision = "0007_article_barcodes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("location", sa.Column("grid_columns", sa.Integer(), nullable=True))
    op.add_column("location", sa.Column("grid_rows", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("location", "grid_rows")
    op.drop_column("location", "grid_columns")
