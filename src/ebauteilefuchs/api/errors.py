"""Translate expected domain errors to safe JSON responses."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from ebauteilefuchs.domain.errors import (
    ActiveChildrenError,
    ArticleNotFoundError,
    BatchConflictError,
    DomainError,
    DuplicateArticleError,
    DuplicateLocationCodeError,
    DuplicateReferenceError,
    IdempotencyConflictError,
    InactiveLocationError,
    InsufficientStockError,
    InventoryConflictError,
    InventoryNotFoundError,
    LocationCycleError,
    LocationInUseError,
    LocationNotFoundError,
    LocationTypeNotFoundError,
    ReferenceNotFoundError,
    SupplierAuthenticationError,
    SupplierNotConfiguredError,
    SupplierRateLimitError,
    SupplierResponseError,
    SupplierUnavailableError,
    ValidationError,
)


def domain_error_response(_: Request, error: DomainError) -> JSONResponse:
    if isinstance(error, SupplierRateLimitError):
        response_status = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(error, SupplierNotConfiguredError):
        response_status = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(error, SupplierAuthenticationError | SupplierResponseError):
        response_status = status.HTTP_502_BAD_GATEWAY
    elif isinstance(error, SupplierUnavailableError):
        response_status = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(
        error,
        (
            ArticleNotFoundError,
            LocationNotFoundError,
            LocationTypeNotFoundError,
            ReferenceNotFoundError,
            InventoryNotFoundError,
        ),
    ):
        response_status = status.HTTP_404_NOT_FOUND
    elif isinstance(
        error,
        (
            ActiveChildrenError,
            BatchConflictError,
            DuplicateLocationCodeError,
            DuplicateArticleError,
            DuplicateReferenceError,
            InactiveLocationError,
            LocationCycleError,
            LocationInUseError,
            IdempotencyConflictError,
            InsufficientStockError,
            InventoryConflictError,
        ),
    ):
        response_status = status.HTTP_409_CONFLICT
    elif isinstance(error, ValidationError):
        response_status = status.HTTP_422_UNPROCESSABLE_CONTENT
    else:
        response_status = status.HTTP_400_BAD_REQUEST
    content: dict = {"detail": error.message, "code": error.code}
    if isinstance(error, DuplicateArticleError):
        content.update(
            {
                "candidate_ids": list(error.candidate_ids),
                "match_level": error.match_level,
                "can_override": error.can_override,
            }
        )
    if isinstance(error, InsufficientStockError):
        content["available"] = error.available
    return JSONResponse(status_code=response_status, content=content)
