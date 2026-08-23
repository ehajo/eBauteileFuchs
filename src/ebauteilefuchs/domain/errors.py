"""Framework-independent application errors with user-safe messages."""


class DomainError(Exception):
    """Base class for expected, user-correctable domain errors."""

    code = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    code = "validation_error"


class LocationNotFoundError(DomainError):
    code = "location_not_found"


class LocationTypeNotFoundError(DomainError):
    code = "location_type_not_found"


class DuplicateLocationCodeError(DomainError):
    code = "duplicate_location_code"


class LocationCycleError(DomainError):
    code = "location_cycle"


class InactiveLocationError(DomainError):
    code = "inactive_location"


class ActiveChildrenError(DomainError):
    code = "active_children"


class BatchConflictError(DomainError):
    code = "batch_conflict"


class ArticleNotFoundError(DomainError):
    code = "article_not_found"


class ReferenceNotFoundError(DomainError):
    code = "reference_not_found"


class DuplicateReferenceError(DomainError):
    code = "duplicate_reference"


class DuplicateArticleError(DomainError):
    code = "duplicate_article"

    def __init__(
        self,
        message: str,
        *,
        candidate_ids: tuple[str, ...],
        match_level: int,
        can_override: bool,
    ) -> None:
        super().__init__(message)
        self.candidate_ids = candidate_ids
        self.match_level = match_level
        self.can_override = can_override
