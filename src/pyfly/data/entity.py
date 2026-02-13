"""Base entity with audit fields for all domain entities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all PyFly entities."""


class BaseEntity(Base):
    """Base entity providing ID and audit trail fields.

    All domain entities should inherit from this class to get automatic
    UUID primary keys and created_at/updated_at/created_by/updated_by tracking.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    created_by: Mapped[str | None] = mapped_column(
        String(255),
        default=None,
    )
    updated_by: Mapped[str | None] = mapped_column(
        String(255),
        default=None,
    )
