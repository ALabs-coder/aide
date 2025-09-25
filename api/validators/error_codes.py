"""
Error codes and messages for PDF validation.

This module defines all possible error codes that can be returned
during PDF validation, with corresponding user-friendly messages.
"""

from enum import Enum


class ErrorCode(Enum):
    """Enumeration of all possible PDF validation error codes."""

    VALID = "VALID"
    NOT_PDF = "NOT_PDF"
    CORRUPTED = "CORRUPTED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    ENCRYPTED_NO_PASSWORD = "ENCRYPTED_NO_PASSWORD"
    WRONG_PASSWORD = "WRONG_PASSWORD"
    NO_TEXT_CONTENT = "NO_TEXT_CONTENT"
    EMPTY_PDF = "EMPTY_PDF"
    TOO_MANY_PAGES = "TOO_MANY_PAGES"


ERROR_MESSAGES = {
    ErrorCode.VALID: "PDF is valid and ready for processing",
    ErrorCode.NOT_PDF: "File is not a valid PDF document",
    ErrorCode.CORRUPTED: "PDF appears to be corrupted or damaged",
    ErrorCode.FILE_TOO_LARGE: "File size exceeds the maximum allowed limit of 25MB",
    ErrorCode.ENCRYPTED_NO_PASSWORD: "PDF is password protected but no password was provided",
    ErrorCode.WRONG_PASSWORD: "The provided password is incorrect",
    ErrorCode.NO_TEXT_CONTENT: "This appears to be a scanned PDF without extractable text. Please use a text-based PDF.",
    ErrorCode.EMPTY_PDF: "PDF has no pages or is empty",
    ErrorCode.TOO_MANY_PAGES: "PDF has too many pages (maximum allowed is 200)"
}


def get_error_message(error_code: ErrorCode, **kwargs) -> str:
    """
    Get user-friendly error message for the given error code.

    Args:
        error_code: The error code to get message for
        **kwargs: Additional parameters for message formatting

    Returns:
        User-friendly error message
    """
    message = ERROR_MESSAGES.get(error_code, "Unknown validation error")

    # Format message with additional parameters if needed
    if error_code == ErrorCode.FILE_TOO_LARGE and 'file_size_mb' in kwargs:
        return f"File size {kwargs['file_size_mb']:.1f}MB exceeds the maximum allowed limit of 25MB"

    if error_code == ErrorCode.TOO_MANY_PAGES and 'page_count' in kwargs:
        return f"PDF has {kwargs['page_count']} pages, maximum allowed is 200"

    return message