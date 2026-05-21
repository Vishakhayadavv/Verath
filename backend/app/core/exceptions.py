from typing import Optional

from fastapi import HTTPException, status


class VerathException(Exception):
    """Base exception for Verath application."""
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class TranscriptionError(VerathException):
    """Raised when audio transcription fails."""
    pass


class EmbeddingError(VerathException):
    """Raised when embedding generation fails."""
    pass


class LLMError(VerathException):
    """Raised when LLM inference fails."""
    pass


class MemoryStorageError(VerathException):
    """Raised when memory storage operations fail."""
    pass


class QueryError(VerathException):
    """Raised when query operations fail."""
    pass


class AuthenticationError(VerathException):
    """Raised when authentication fails."""
    pass


def http_exception_from_error(error: VerathException) -> HTTPException:
    """Convert VerathException to HTTPException."""
    status_code_map = {
        TranscriptionError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        EmbeddingError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        LLMError: status.HTTP_503_SERVICE_UNAVAILABLE,
        MemoryStorageError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        QueryError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    }

    status_code = status_code_map.get(type(error), status.HTTP_500_INTERNAL_SERVER_ERROR)

    return HTTPException(
        status_code=status_code,
        detail={
            "message": error.message,
            "type": error.__class__.__name__,
            "details": error.details
        }
    )
