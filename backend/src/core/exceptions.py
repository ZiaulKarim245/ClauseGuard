"""
Core Exceptions - Standardized error hierarchy for the ClauseGuard ecosystem.
"""
from fastapi import HTTPException, status

class ClauseGuardException(Exception):
    """Base exception for all domain-specific ClauseGuard errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

# --- Specialist Error Types ---

class QuotaExhaustedError(ClauseGuardException):
    """Signals that an AI provider (Groq, Google) has hit usage or rate limits."""
    def __init__(self, provider: str):
        super().__init__(
            message=f"Legal Analysis Quota for {provider} exceeded. Fallback active.",
            code="QUOTA_EXHAUSTED"
        )

class DocumentParsingError(ClauseGuardException):
    """Signals a failure in OCR or structural text extraction from a contract file."""
    def __init__(self, filename: str):
        super().__init__(
            message=f"Failed to analyze structure of {filename}. File may be corrupt or encrypted.",
            code="PARSING_FAILURE"
        )

class LegalResearchError(ClauseGuardException):
    """Signals a failure during external judicial precedent or statute searches."""
    def __init__(self, detail: str):
        super().__init__(
            message=f"Precedent research failed: {detail}",
            code="RESEARCH_ERROR"
        )

    @staticmethod
    def is_quota_error(e: Exception) -> bool:
        """Utility to detect if a raw exception originates from rate/token limits."""
        msg = str(e).upper()
        return any(x in msg for x in ["429", "RESOURCE_EXHAUSTED", "RATE_LIMIT"])

# --- Interface Handlers ---

def handle_custom_exception(exc: ClauseGuardException) -> HTTPException:
    """Maps internal domain exceptions to professional FastAPI HTTP responses."""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"message": exc.message, "code": exc.code}
    )
