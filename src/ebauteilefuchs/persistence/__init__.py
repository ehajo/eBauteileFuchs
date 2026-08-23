"""Persistence adapters for eBauteileFuchs."""

from ebauteilefuchs.persistence.database import Base, create_database_engine

__all__ = ["Base", "create_database_engine"]
