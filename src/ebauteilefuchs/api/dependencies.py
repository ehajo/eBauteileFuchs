"""Shared FastAPI dependency helpers."""

from collections.abc import Callable

from fastapi import Request

from ebauteilefuchs.application.locations import LocationService


def get_location_service(request: Request) -> LocationService:
    factory: Callable[[], LocationService] = request.app.state.location_service_factory
    return factory()


def request_base_url(request: Request) -> str:
    configured = request.app.state.settings.public_base_url
    return configured.rstrip("/") if configured else str(request.base_url).rstrip("/")
