"""Add M3 inventory balances, immutable journal, and transactions.

Revision ID: 0004_m3_inventory
Revises: 0003_m2_articles
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_m3_inventory"
down_revision: str | None = "0003_m2_articles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inventory_balance",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("article_id", sa.String(36), nullable=False),
        sa.Column("location_id", sa.String(36), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 8), nullable=False),
        sa.Column("unit", sa.String(24), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("quantity >= 0", name="ck_inventory_balance_non_negative"),
        sa.CheckConstraint("version >= 1", name="ck_inventory_balance_version"),
        sa.ForeignKeyConstraint(["article_id"], ["article.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["location_id"], ["location.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "article_id", "location_id", "unit", name="uq_inventory_balance_key"
        ),
    )
    op.create_index(
        "ix_inventory_balance_article_id", "inventory_balance", ["article_id"]
    )
    op.create_index(
        "ix_inventory_balance_location_id", "inventory_balance", ["location_id"]
    )

    op.create_table(
        "inventory_transaction",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("transaction_type", sa.String(16), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "transaction_type IN ('stock_in', 'stock_out', 'transfer', "
            "'adjustment', 'initial')",
            name="ck_inventory_transaction_type",
        ),
        sa.UniqueConstraint("idempotency_key", name="uq_inventory_transaction_key"),
    )
    op.create_index(
        "ix_inventory_transaction_created_at",
        "inventory_transaction",
        ["created_at"],
    )

    op.create_table(
        "inventory_movement",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("transaction_id", sa.String(36), nullable=False),
        sa.Column("article_id", sa.String(36), nullable=False),
        sa.Column("location_id", sa.String(36), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(24, 8), nullable=False),
        sa.Column("unit", sa.String(24), nullable=False),
        sa.Column("balance_after", sa.Numeric(24, 8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "quantity_delta <> 0", name="ck_inventory_movement_non_zero"
        ),
        sa.CheckConstraint(
            "balance_after >= 0", name="ck_inventory_movement_balance_non_negative"
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"], ["inventory_transaction.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["article_id"], ["article.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["location_id"], ["location.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_inventory_movement_transaction_id",
        "inventory_movement",
        ["transaction_id"],
    )
    op.create_index(
        "ix_inventory_movement_article_created",
        "inventory_movement",
        ["article_id", "created_at"],
    )
    op.create_index(
        "ix_inventory_movement_location_created",
        "inventory_movement",
        ["location_id", "created_at"],
    )
    for table in ("inventory_movement", "inventory_transaction"):
        op.execute(
            f"CREATE TRIGGER trg_{table}_immutable_update "
            f"BEFORE UPDATE ON {table} BEGIN "
            "SELECT RAISE(ABORT, 'inventory journal is immutable'); END"
        )
        op.execute(
            f"CREATE TRIGGER trg_{table}_immutable_delete "
            f"BEFORE DELETE ON {table} BEGIN "
            "SELECT RAISE(ABORT, 'inventory journal is immutable'); END"
        )


def downgrade() -> None:
    for table in ("inventory_movement", "inventory_transaction"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable_delete")
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable_update")
    op.drop_index(
        "ix_inventory_movement_location_created", table_name="inventory_movement"
    )
    op.drop_index(
        "ix_inventory_movement_article_created", table_name="inventory_movement"
    )
    op.drop_index(
        "ix_inventory_movement_transaction_id", table_name="inventory_movement"
    )
    op.drop_table("inventory_movement")
    op.drop_index(
        "ix_inventory_transaction_created_at", table_name="inventory_transaction"
    )
    op.drop_table("inventory_transaction")
    op.drop_index("ix_inventory_balance_location_id", table_name="inventory_balance")
    op.drop_index("ix_inventory_balance_article_id", table_name="inventory_balance")
    op.drop_table("inventory_balance")
