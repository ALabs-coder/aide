"""
Data structures for PDF validation results.

This module defines the result structures returned by PDF validation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any
from .error_codes import ErrorCode


class PDFType(Enum):
    """Classification of PDF content type."""
    TEXT_BASED = "text"
    SCANNED = "scanned"
    HYBRID = "hybrid"
    INVALID = "invalid"


@dataclass
class ValidationResult:
    """
    Result of PDF validation process.

    This structure contains all information about whether a PDF
    can be processed and any issues found during validation.
    """

    is_valid: bool
    """Whether the PDF passed all validation checks and can be processed."""

    pdf_type: PDFType
    """Classification of the PDF content type."""

    error_code: ErrorCode
    """Specific error code if validation failed."""

    error_message: str
    """User-friendly error message explaining the validation result."""

    metadata: Dict[str, Any]
    """Additional information about the PDF (page count, size, etc)."""

    confidence_score: float
    """Confidence level of the validation (0.0 to 1.0)."""

    def __post_init__(self):
        """Validate the result structure after initialization."""
        # Ensure confidence score is within valid range
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(f"Confidence score must be between 0.0 and 1.0, got {self.confidence_score}")

        # Ensure metadata is a dictionary
        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        # Valid PDFs should have VALID error code and high confidence
        if self.is_valid and self.error_code != ErrorCode.VALID:
            raise ValueError("Valid PDFs must have ErrorCode.VALID")

        # Invalid PDFs should not have VALID error code
        if not self.is_valid and self.error_code == ErrorCode.VALID:
            raise ValueError("Invalid PDFs cannot have ErrorCode.VALID")