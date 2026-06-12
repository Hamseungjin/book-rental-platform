class BookRentalError(Exception):
    """Base error shown to application users."""


class NotFoundError(BookRentalError):
    """Raised when a requested record does not exist."""


class AuthorizationError(BookRentalError):
    """Raised when an actor does not have the required role."""


class ValidationError(BookRentalError):
    """Raised when a business invariant is violated."""
