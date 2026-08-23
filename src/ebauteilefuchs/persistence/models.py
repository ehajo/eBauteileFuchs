"""SQLAlchemy persistence models for M1 locations."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
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
