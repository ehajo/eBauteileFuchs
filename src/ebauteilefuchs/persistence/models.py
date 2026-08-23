"""SQLAlchemy persistence models for M1 locations."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
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
