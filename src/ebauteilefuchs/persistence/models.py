"""SQLAlchemy persistence models for the M0 through M3 schema."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DDL,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from ebauteilefuchs.persistence.database import Base


class LocationTypeModel(Base):
    __tablename__ = "location_type"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (UniqueConstraint("code", name="uq_location_type_code"),)


class LocationModel(Base):
    __tablename__ = "location"
    __table_args__ = (
        UniqueConstraint(
            "parent_scope",
            "normalized_code",
            name="uq_location_parent_scope_normalized_code",
        ),
        UniqueConstraint("qr_token", name="uq_location_qr_token"),
        CheckConstraint(
            "parent_scope = COALESCE(parent_id, '__root__')",
            name="ck_location_parent_scope",
        ),
        Index("ix_location_parent_id", "parent_id"),
        Index("ix_location_location_type_id", "location_type_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location_type_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("location_type.id", ondelete="RESTRICT"), nullable=False
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("location.id", ondelete="RESTRICT"), nullable=True
    )
    parent_scope: Mapped[str] = mapped_column(String(36), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    qr_token: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    grid_columns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grid_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ManufacturerModel(Base):
    __tablename__ = "manufacturer"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_manufacturer_normalized_name"),
        Index("ix_manufacturer_normalized_name", "normalized_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class CategoryModel(Base):
    __tablename__ = "category"
    __table_args__ = (UniqueConstraint("code", name="uq_category_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)


class SupplierModel(Base):
    __tablename__ = "supplier"
    __table_args__ = (UniqueConstraint("code", name="uq_supplier_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    adapter_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AttributeDefinitionModel(Base):
    __tablename__ = "attribute_definition"
    __table_args__ = (UniqueConstraint("code", name="uq_attribute_definition_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    value_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    canonical_unit: Mapped[str | None] = mapped_column(String(24), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CategoryAttributeModel(Base):
    __tablename__ = "category_attribute"

    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("category.id", ondelete="CASCADE"), primary_key=True
    )
    attribute_definition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("attribute_definition.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_typical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allowed_units_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")


class ArticleModel(Base):
    __tablename__ = "article"
    __table_args__ = (
        UniqueConstraint(
            "manufacturer_id",
            "normalized_manufacturer_part_number",
            name="uq_article_manufacturer_normalized_part_number",
        ),
        Index("ix_article_category_id", "category_id"),
        Index("ix_article_manufacturer_id", "manufacturer_id"),
        Index("ix_article_search_text", "search_text"),
        Index(
            "ix_article_normalized_manufacturer_part_number",
            "normalized_manufacturer_part_number",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    manufacturer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("manufacturer.id", ondelete="RESTRICT"), nullable=True
    )
    manufacturer_part_number: Mapped[str | None] = mapped_column(
        String(160), nullable=True
    )
    normalized_manufacturer_part_number: Mapped[str | None] = mapped_column(
        String(160), nullable=True
    )
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("category.id", ondelete="RESTRICT"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    datasheet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    product_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class ArticleBarcodeCompatibilityModel(Base):
    """Persisted M5 compatibility table; no application feature reads it."""

    __tablename__ = "article_barcode"
    __table_args__ = (
        UniqueConstraint(
            "normalized_value", name="uq_article_barcode_normalized_value"
        ),
        Index("ix_article_barcode_article_id", "article_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("article.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class ArticleAttributeModel(Base):
    __tablename__ = "article_attribute"
    __table_args__ = (
        CheckConstraint(
            "(attribute_definition_id IS NOT NULL AND custom_name IS NULL) OR "
            "(attribute_definition_id IS NULL AND custom_name IS NOT NULL)",
            name="ck_article_attribute_definition_or_custom",
        ),
        Index("ix_article_attribute_article_id", "article_id"),
        Index("ix_article_attribute_normalized_text", "normalized_text"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("article.id", ondelete="CASCADE"), nullable=False
    )
    attribute_definition_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("attribute_definition.id", ondelete="RESTRICT"),
        nullable=True,
    )
    custom_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_value: Mapped[str] = mapped_column(String(240), nullable=False)
    normalized_text: Mapped[str] = mapped_column(String(240), nullable=False)
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(24), nullable=True)
    canonical_numeric_value: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 8), nullable=True
    )
    canonical_unit: Mapped[str | None] = mapped_column(String(24), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class SupplierPartModel(Base):
    __tablename__ = "supplier_part"
    __table_args__ = (
        UniqueConstraint(
            "supplier_id",
            "normalized_supplier_part_number",
            name="uq_supplier_part_supplier_normalized_number",
        ),
        Index("ix_supplier_part_article_id", "article_id"),
        Index(
            "ix_supplier_part_normalized_supplier_part_number",
            "normalized_supplier_part_number",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("article.id", ondelete="CASCADE"), nullable=False
    )
    supplier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier.id", ondelete="RESTRICT"), nullable=False
    )
    supplier_part_number: Mapped[str] = mapped_column(String(160), nullable=False)
    normalized_supplier_part_number: Mapped[str] = mapped_column(
        String(160), nullable=False
    )
    product_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class SupplierCacheEntryModel(Base):
    __tablename__ = "supplier_cache_entry"
    __table_args__ = (
        UniqueConstraint(
            "supplier_id",
            "query_type",
            "query_normalized",
            "adapter_version",
            name="uq_supplier_cache_lookup",
        ),
        Index("ix_supplier_cache_expires_at", "expires_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier.id", ondelete="CASCADE"), nullable=False
    )
    query_type: Mapped[str] = mapped_column(String(40), nullable=False)
    query_normalized: Mapped[str] = mapped_column(String(160), nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(40), nullable=False)
    response_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class InventoryBalanceModel(Base):
    __tablename__ = "inventory_balance"
    __table_args__ = (
        UniqueConstraint(
            "article_id", "location_id", "unit", name="uq_inventory_balance_key"
        ),
        CheckConstraint("quantity >= 0", name="ck_inventory_balance_non_negative"),
        CheckConstraint("version >= 1", name="ck_inventory_balance_version"),
        Index("ix_inventory_balance_article_id", "article_id"),
        Index("ix_inventory_balance_location_id", "location_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("article.id", ondelete="RESTRICT"), nullable=False
    )
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("location.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    unit: Mapped[str] = mapped_column(String(24), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class InventoryTransactionModel(Base):
    __tablename__ = "inventory_transaction"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_inventory_transaction_key"),
        CheckConstraint(
            "transaction_type IN ('stock_in', 'stock_out', 'transfer', "
            "'adjustment', 'initial')",
            name="ck_inventory_transaction_type",
        ),
        Index("ix_inventory_transaction_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    transaction_type: Mapped[str] = mapped_column(String(16), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class InventoryMovementModel(Base):
    __tablename__ = "inventory_movement"
    __table_args__ = (
        CheckConstraint("quantity_delta <> 0", name="ck_inventory_movement_non_zero"),
        CheckConstraint(
            "balance_after >= 0", name="ck_inventory_movement_balance_non_negative"
        ),
        Index("ix_inventory_movement_transaction_id", "transaction_id"),
        Index("ix_inventory_movement_article_created", "article_id", "created_at"),
        Index("ix_inventory_movement_location_created", "location_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("inventory_transaction.id", ondelete="RESTRICT"),
        nullable=False,
    )
    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("article.id", ondelete="RESTRICT"), nullable=False
    )
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("location.id", ondelete="RESTRICT"), nullable=False
    )
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    unit: Mapped[str] = mapped_column(String(24), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


for table, name in (
    (InventoryMovementModel.__table__, "inventory_movement"),
    (InventoryTransactionModel.__table__, "inventory_transaction"),
):
    event.listen(
        table,
        "after_create",
        DDL(
            f"CREATE TRIGGER trg_{name}_immutable_update "
            f"BEFORE UPDATE ON {name} BEGIN "
            "SELECT RAISE(ABORT, 'inventory journal is immutable'); END"
        ).execute_if(dialect="sqlite"),
    )
    event.listen(
        table,
        "after_create",
        DDL(
            f"CREATE TRIGGER trg_{name}_immutable_delete "
            f"BEFORE DELETE ON {name} BEGIN "
            "SELECT RAISE(ABORT, 'inventory journal is immutable'); END"
        ).execute_if(dialect="sqlite"),
    )
