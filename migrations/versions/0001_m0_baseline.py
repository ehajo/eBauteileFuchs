"""Create the M0 schema baseline.

Revision ID: 0001_m0_baseline
Revises:
Create Date: 2026-08-23
"""

revision: str = "0001_m0_baseline"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Reserve a clean baseline before the first domain tables in M1."""


def downgrade() -> None:
    """Return to the empty pre-M0 schema."""
