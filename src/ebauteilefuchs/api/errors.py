"""Translate expected domain errors to safe JSON responses."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from ebauteilefuchs.domain.errors import (
    ActiveChildrenError,
    BatchConflictError,
    DomainError,
    DuplicateLocationCodeError,
    InactiveLocationError,
    LocationCycleError,
    LocationNotFoundError,
    LocationTypeNotFoundError,
    ValidationError,
)


def domain_error_response(_: Request, error: DomainError) -> JSONResponse:
    if isinstance(error, (LocationNotFoundError, LocationTypeNotFoundError)):
        response_status = status.HTTP_404_NOT_FOUND
    elif isinstance(
        error,
        (
            ActiveChildrenError,
            BatchConflictError,
            DuplicateLocationCodeError,
            InactiveLocationError,
            LocationCycleError,
        ),
    ):
        response_status = status.HTTP_409_CONFLICT
    elif isinstance(error, ValidationError):
        response_status = status.HTTP_422_UNPROCESSABLE_CONTENT
    else:
        response_status = status.HTTP_400_BAD_REQUEST
    return JSONResponse(
        status_code=response_status,
        content={"detail": error.message, "code": error.code},
    )
