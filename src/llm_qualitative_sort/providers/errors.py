"""Shared error handling utilities for LLM providers."""

from llm_qualitative_sort.models import ComparisonResult


def create_error_result(error: Exception, error_type: str, prefix: str) -> ComparisonResult:
    """Create a ComparisonResult for an error condition.

    Provides unified error handling across all LLM providers, ensuring
    consistent error response format.

    Args:
        error: The exception that occurred
        error_type: Category of error (e.g., "rate_limit", "timeout", "connection")
        prefix: Human-readable prefix for the reasoning (e.g., "Rate limit exceeded")

    Returns:
        ComparisonResult with winner=None and error details
    """
    return ComparisonResult(
        winner=None,
        reasoning=f"{prefix}: {error}",
        raw_response={"error": str(error), "error_type": error_type}
    )
