"""Operational health endpoint."""

from typing import Literal

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ebauteilefuchs import __version__
from ebauteilefuchs.persistence.database import check_database

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    database: Literal["ok"]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Prüft Anwendung und Datenbank",
)
def health(request: Request) -> HealthResponse | JSONResponse:
    try:
        check_database(request.app.state.database_engine)
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "service": "eBauteileFuchs",
                "version": __version__,
                "database": "error",
            },
        )
    return HealthResponse(
        status="ok",
        service="eBauteileFuchs",
        version=__version__,
        database="ok",
    )
